"""Grounded answering with verification, adapted from MedEvolv Mentor's rag/answer.py + rag/drug_check.py.

Pipeline for one question (after the agent's guard rails and retrieval have run):

    evidence = build_evidence(query, docs)      numbered passages [1]..[n]: header + headline + filing-PDF excerpt
    draft    = LLM(SYSTEM, evidence, query)     temperature 0, told to cite every claim and to reply
                                                INSUFFICIENT_CONTEXT when the evidence doesn't answer it
    problems = verify(draft, evidence)          deterministic checks, no LLM:
                                                  - every factual sentence cites [n] that exists
                                                  - every number in a sentence appears in the passages it cites
                                                  - every company named appears in the passages it cites
    if problems: one temperature-0 rewrite, accepted only if it adds no new number or citation and passes verify;
                 otherwise the failing sentences are dropped (never shown to the user)
    nothing verified left -> decline with "I don't know"

Every stage is recorded as a trace step that the UI shows, so the reasoning path is visible and checkable.
"""
from __future__ import annotations

import functools
import os
import re
import time
from dataclasses import dataclass, field

import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENRICHED_CSV = os.path.join(BASE_DIR, "data", "filings_enriched.csv")

MAX_EVIDENCE = 8
EXCERPT_CHARS = 900
MODELS = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]

REFUSAL = "I don't know. That is not present in the 7-day NSE filings database (Nov 9–15, 2026)."
INSUFFICIENT_DETAIL = ("The filings I found for this question don't actually state the answer, so I won't guess. "
                       "Open the source filings below to check them yourself.")

SYSTEM = """You are Market Tide Mentor, an assistant that answers questions about Indian stock-exchange filings.
Your only knowledge is the numbered evidence passages: official NSE corporate filings published 9-15 Nov 2026.
Rules:
- Answer ONLY from the numbered evidence passages. Do not use outside knowledge: no share prices, company history,
  background or events that the passages do not state.
- Cite every factual sentence or bullet with its passage number(s) in square brackets, e.g. [2] or [1][3].
  Use only passage numbers that exist. In a list, give every item (e.g. every company) its own bullet and citation.
- Copy numbers, amounts, ratios, dates and names exactly as the passages write them. Do not convert units,
  calculate totals, round, estimate or compare magnitudes the passages do not compare.
- Do not interpret or predict: no "bullish", "bearish", "positive/negative for investors", price impact or advice.
- If the evidence does not contain the answer, reply exactly: INSUFFICIENT_CONTEXT
- If only part of the question is covered, answer that part and say plainly which part the filings do not cover.
- Be concise: a one-line answer, then short bullet points. Start directly with the answer; do not repeat the
  passage headers or source lines. Do not use tables."""

REPAIR = """Your draft answer failed an automatic fact check against the evidence. Problems found:
{problems}

Rewrite the answer so that every sentence is supported by the passages it cites. Fix or remove each problem
sentence. Do not add any new fact, number or citation that is not already in the draft. Keep the same rules:
cite every factual sentence as [n], copy numbers exactly, no outside knowledge. If nothing supported remains,
reply exactly: INSUFFICIENT_CONTEXT

Draft answer:
{draft}"""

# A sentence that only says what the filings do NOT cover needs no citation (MedEvolv: "state plainly which part
# the sources do not cover").
DISCLOSURE = re.compile(
    r"\b(not (covered|mentioned|stated|available|disclosed|included|provided|specified|present|given|found)|"
    r"do(es)? not (contain|mention|state|specify|include|provide|cover|disclose|give)|"
    r"no (information|details|data|mention|figures?)|(isn't|aren't|wasn't|weren't) (stated|given|disclosed|mentioned))\b",
    re.I)
CITE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\]")
# A number not glued to a preceding letter ("FY27", "Q2", "H1" are labels, not figures). Units glued after it
# ("1,303crore", "5.15GWh") are fine.
NUMBER = re.compile(r"(?<![A-Za-z0-9])\d[\d,]*(?:\.\d+)?")
CURRENCY_GLUE = re.compile(r"(INR|Rs\.?|Re\.?|USD|US\$)(?=\d)", re.I)      # "INR1,303" -> "INR 1,303"
PERIOD_SPACE = re.compile(r"\b(FY|Q|H)\s+(?=\d)", re.I)                     # "FY 27" -> "FY27"


@dataclass
class Evidence:
    n: int
    doc: dict
    text: str


@dataclass
class Result:
    text: str
    status: str = "answered"      # answered | repaired | trimmed | insufficient | no_llm
    evidence: list = field(default_factory=list)
    cited: list = field(default_factory=list)          # 1-based passage numbers cited in the final text
    steps: list = field(default_factory=list)          # trace steps in the app's format
    problems: list = field(default_factory=list)       # problems found in the draft
    removed: list = field(default_factory=list)        # sentences dropped because they couldn't be verified
    body: str = ""                                     # the verified answer itself, without the system notes
    model: str = ""


# ---------------------------------------------------------------- evidence

@functools.lru_cache(maxsize=1)
def _bodies() -> dict:
    if not os.path.exists(ENRICHED_CSV):
        return {}
    df = pd.read_csv(ENRICHED_CSV, dtype=str, keep_default_na=False, usecols=["id", "body"])
    return {r.id: r.body for r in df.itertuples() if r.body}


def _clean_val(v) -> str:
    s = "" if v is None else str(v).strip()
    return "" if s.lower() in {"nan", "none", "null", "n/a", ""} else s


def _tokens(text: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", text.lower()) if len(t) > 2}


BOILER = re.compile(r"yours (faithfully|truly|sincerely)|thanking you|dear sir|company secretary|compliance officer|"
                    r"\bdin\b|membership no|scrip code|listing (department|compliance)|dalal street|bandra.kurla|"
                    r"take (the )?(above|same) on (your )?record|kindly take", re.I)


def _excerpt(body: str, query: str, limit: int = EXCERPT_CHARS) -> str:
    """Pick the sentences of a filing that best match the question (numbers and amounts get a bonus)."""
    if not body:
        return ""
    sents = [s.strip() for s in re.split(r"(?<=[.;])\s+|\n", body) if len(s.strip()) > 20 and not BOILER.search(s)]
    q = _tokens(query)
    scored = sorted(range(len(sents)), key=lambda i: -(2 * len(q & _tokens(sents[i]))
                                                        + (1 if re.search(r"\d", sents[i]) else 0)
                                                        + (2 if re.search(r"(rs\.?|₹|crore|lakh|%|per share)", sents[i], re.I) else 0)))
    keep, size = [], 0
    for i in scored:
        if size + len(sents[i]) > limit:
            continue
        keep.append(i)
        size += len(sents[i]) + 1
    return " ".join(sents[i] for i in sorted(keep))


def build_evidence(query: str, docs: list[dict], facts: list[str] | None = None) -> list[Evidence]:
    """facts = extra statements computed from the database itself (e.g. the total number of matching filings),
    numbered after the filings so the answer can cite them too."""
    bodies = _bodies()
    out = []
    for n, d in enumerate(docs[:MAX_EVIDENCE], 1):
        head = (f"[{n}] Source: {_clean_val(d.get('company'))} (NSE: {_clean_val(d.get('ticker'))}) · "
                f"{_clean_val(d.get('date'))} {_clean_val(d.get('time'))} · {_clean_val(d.get('category'))}")
        lines = [head, f"Headline: {_clean_val(d.get('headline'))}"]
        summary = _clean_val(d.get("summary"))
        if summary:
            lines.append(f"Summary: {summary}")
        ex = _excerpt(bodies.get(str(d.get("id")), ""), query)
        lines.append(f"Filing text excerpt: {ex}" if ex else "Filing text excerpt: (not available: scanned or unreadable PDF)")
        out.append(Evidence(n, d, "\n".join(lines)))
    for f in facts or []:
        n = len(out) + 1
        out.append(Evidence(n, None, f"[{n}] Source: Market Tide database count (computed, not an LLM)\n{f}"))
    return out


# ---------------------------------------------------------------- verification

def _norm_num(s: str) -> str:
    s = s.replace(",", "")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s.lstrip("0") or "0"


def _numbers(text: str) -> set:
    t = CURRENCY_GLUE.sub(r"\1 ", PERIOD_SPACE.sub(r"\1", CITE.sub(" ", text)))
    return {_norm_num(m) for m in NUMBER.findall(t)}


def _cites(text: str) -> list[int]:
    out = []
    for grp in CITE.findall(text):
        for part in re.split(r"\s*,\s*", grp):
            if re.search(r"[–-]", part):
                a, b = re.split(r"\s*[–-]\s*", part)[:2]
                if a.isdigit() and b.isdigit() and int(b) - int(a) < 20:
                    out += list(range(int(a), int(b) + 1))
            elif part.strip().isdigit():
                out.append(int(part))
    return out


def _units(text: str) -> list[str]:
    """Answer -> checkable units: lines, and sentences inside long lines. Table separator rows are skipped."""
    units = []
    for line in text.splitlines():
        s = line.strip()
        if not s or re.fullmatch(r"[|:\-\s]+", s):
            continue
        parts = [p.strip() for p in (re.split(r"(?<=[.!?])\s+(?=[A-Z*•\-])", s) if len(s) > 160 else [s]) if p.strip()]
        # A citation at the end of a line covers the uncited sentences before it in that line (paragraph-level
        # citation); their numbers and names are still checked against that cited passage.
        tail = CITE.findall(parts[-1]) if parts else []
        if len(parts) > 1 and tail:
            marker = "".join(f"[{g}]" for g in tail)
            parts = [p if CITE.search(p) else f"{p} {marker}" for p in parts]
        units += parts
    return units


def _is_heading(u: str) -> bool:
    bare = re.sub(r"[#*_`>•\-:|]", " ", u).strip()
    return (u.lstrip().startswith("#") or len(bare.split()) <= 6) and not NUMBER.search(CITE.sub(" ", u))


@functools.lru_cache(maxsize=1)
def _company_names() -> tuple:
    """Normalised company names in the whole dataset, used to spot a company named without support."""
    try:
        df = pd.read_csv(ENRICHED_CSV, dtype=str, keep_default_na=False, usecols=["company", "ticker"])
    except Exception:
        return ()
    names = set()
    for c in df.company.unique():
        n = _norm_name(c)
        if len(n) >= 8 and len(n.split()) >= 2:
            names.add(n)
    return tuple(sorted(names, key=len, reverse=True))


def _norm_name(s: str) -> str:
    s = re.sub(r"\b(limited|ltd|pvt|private|the)\b\.?", " ", s.lower().replace("&", " and "))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s)).strip()


def verify(text: str, evidence: list[Evidence]) -> list[dict]:
    """Deterministic fact check. Returns one problem per failing unit: {"unit", "why"}."""
    n_ev = len(evidence)
    ev_nums = {e.n: _numbers(e.text) for e in evidence}
    ev_names = {e.n: _norm_name(e.text) for e in evidence}
    problems = []
    for u in _units(text):
        cites = _cites(u)
        invalid = sorted({c for c in cites if not 1 <= c <= n_ev})
        if invalid:
            problems.append({"unit": u, "why": f"cites passage(s) {invalid} that do not exist"})
            continue
        if DISCLOSURE.search(u) and not _numbers(u):
            continue                                   # "the filings do not state X" needs no citation
        if not cites:
            if _is_heading(u):
                continue
            problems.append({"unit": u, "why": "makes a claim without citing a passage"})
            continue
        pool_nums = set().union(*(ev_nums[c] for c in cites))
        missing = sorted(x for x in _numbers(u) - pool_nums if len(x) >= 1)
        if missing:
            problems.append({"unit": u, "why": f"number(s) {missing} do not appear in the cited passage(s) {sorted(set(cites))}"})
            continue
        pool_names = " ".join(ev_names[c] for c in cites)
        nu = " " + _norm_name(u) + " "
        for name in _company_names():
            if f" {name} " in nu and name not in pool_names:
                problems.append({"unit": u, "why": f"names '{name}' which is not in the cited passage(s)"})
                break
    return problems


def _drop(text: str, problems: list[dict]) -> tuple[str, list[str]]:
    bad = {p["unit"] for p in problems}
    kept, removed = [], []
    for line in text.splitlines():
        s = line.strip()
        units = _units(s) if s else []
        if units and any(u in bad for u in units):
            good = [u for u in units if u not in bad]
            removed += [u for u in units if u in bad]
            if good:
                prefix = line[:len(line) - len(line.lstrip())]
                kept.append(prefix + " ".join(good))
        else:
            kept.append(line)
    out = "\n".join(kept).strip()
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out, removed


def _has_supported_claim(text: str, n_ev: int) -> bool:
    return any(_cites(u) and all(1 <= c <= n_ev for c in _cites(u)) for u in _units(text))


# ---------------------------------------------------------------- LLM

LEADING_JUNK = re.compile(r"^\s*(?:\[\d+\]\s*)+(?:Source:.*)?$")


def _clean(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()
    # gpt-oss writes citations as 【2】 or 【2†L4-L9】: normalise to [2] so they can be checked
    text = re.sub(r"【\s*(\d+)[^】]*】", r"[\1]", text)
    text = re.sub(r"\[\s*(\d+)\s*†[^\]]*\]", r"[\1]", text)
    lines = text.splitlines()
    while lines and (LEADING_JUNK.match(lines[0]) or not lines[0].strip()):
        lines.pop(0)
    return "\n".join(lines).strip()


def _chat(client, system: str, user: str) -> tuple[str, str]:
    last = None
    for model in MODELS:
        kw = {"reasoning_effort": "low"} if model.startswith("openai/gpt-oss") else {}
        for attempt in range(2):
            try:
                r = client.chat.completions.create(
                    model=model, temperature=0, max_tokens=2000,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
                text = r.choices[0].message.content or ""
                if text.strip():
                    return _clean(text), model
                last = f"{model}: empty reply"
                break
            except Exception as e:
                last = f"{model}: {type(e).__name__}: {str(e)[:120]}"
                # Groq's free tier is 8k tokens/minute per model. A short wait keeps the strongest model instead of
                # falling back to a weaker one (weaker models cite less reliably, so more gets trimmed).
                m = re.search(r"try again in ([\d.]+)\s*(ms|s)", str(e))
                wait = (float(m.group(1)) / (1000 if m.group(2) == "ms" else 1)) if m else None
                if attempt == 0 and wait is not None and wait <= 12:
                    time.sleep(wait + 0.5)
                    continue
                break                                 # model gone, network, long wait: try the next model
    raise RuntimeError(last or "no model available")


def _step(stage, icon, title, detail, status="good", ms=0.0, **extra):
    return {"stage": stage, "icon": icon, "title": title, "detail": detail, "status": status, "ms": ms, **extra}


def answer(client, query: str, docs: list[dict], history: list[dict] | None = None,
           facts: list[str] | None = None) -> Result:
    evidence = build_evidence(query, docs, facts)
    res = Result(text="", evidence=evidence)
    with_text = sum(1 for e in evidence if e.doc is not None and "not available" not in e.text)
    res.steps.append(_step("evidence", "📋", f"{len(evidence)} numbered passages assembled",
                           f"{with_text} include text from the filing PDF; the rest have only the headline. "
                           "The model may answer only from these and must cite each claim as [n]."))
    if client is None:
        res.status = "no_llm"
        res.text = "\n".join(f"- **{_clean_val(e.doc.get('company'))}** ({_clean_val(e.doc.get('date'))}): "
                             f"{_clean_val(e.doc.get('headline'))} [{e.n}]" for e in evidence if e.doc is not None)
        res.cited = [e.n for e in evidence]
        res.steps.append(_step("llm", "🤖", "No language model key", "Showing the filings' own headlines instead "
                               "of a written answer.", status="warn"))
        return res

    prev = [m["content"] for m in (history or []) if m.get("role") == "user"][-2:]
    context = ("Earlier questions in this chat (context only, NOT evidence): " + " | ".join(prev) + "\n\n") if prev else ""
    prompt = ("Evidence passages:\n\n" + "\n\n".join(e.text for e in evidence)
              + f"\n\n{context}Question: {query}\nAnswer:")

    t = time.time()
    try:
        draft, res.model = _chat(client, SYSTEM, prompt)
    except RuntimeError as e:
        res.status = "insufficient"
        res.text = REFUSAL + "\n\nThe language model could not be reached, so I won't answer without it."
        res.steps.append(_step("llm", "🤖", "Language model unavailable", str(e)[:200], status="stop",
                               ms=(time.time() - t) * 1000))
        return res
    res.steps.append(_step("llm", "🤖", "Draft answer written", f"{res.model}, temperature 0, evidence only.",
                           ms=(time.time() - t) * 1000))

    if "INSUFFICIENT_CONTEXT" in draft:
        res.status = "insufficient"
        res.text = REFUSAL + "\n\n" + INSUFFICIENT_DETAIL
        res.steps.append(_step("refuse", "⛔", "Declined: evidence insufficient",
                               "The model read the passages and found they do not answer the question.", status="stop"))
        return res

    t = time.time()
    problems = verify(draft, evidence)
    res.problems = problems
    final = draft
    if not problems:
        res.steps.append(_step("verify", "🔎", "Fact check passed",
                               "Every claim cites a real passage; every number and company named appears in the "
                               "passages it cites.", ms=(time.time() - t) * 1000))
    else:
        res.steps.append(_step("verify", "🔎", f"Fact check found {len(problems)} problem(s)",
                               "; ".join(f"\"{p['unit'][:70]}\" {p['why']}" for p in problems[:4]),
                               status="warn", ms=(time.time() - t) * 1000))
        # One repair attempt, validated like MedEvolv's drug-check rewrite: it may not add numbers or citations.
        t = time.time()
        fixed = ""
        try:
            fixed, _ = _chat(client, SYSTEM, prompt + "\n\n" + REPAIR.format(
                problems="\n".join(f"- \"{p['unit']}\": {p['why']}" for p in problems), draft=draft))
        except RuntimeError:
            pass
        # Accept the rewrite only if it passes the full check and introduces no number the draft didn't have.
        # (Adding citations is allowed: that is usually the fix, and verify() proves each one is real and
        # that every number sits in the passage it cites.)
        ok = (fixed and "INSUFFICIENT_CONTEXT" not in fixed and not verify(fixed, evidence)
              and _numbers(fixed) <= _numbers(draft))
        if ok:
            final, res.status = fixed, "repaired"
            res.steps.append(_step("repair", "🛠️", "Answer rewritten and re-checked",
                                   "The rewrite passed the fact check and added no new number or citation.",
                                   ms=(time.time() - t) * 1000))
        else:
            # Drop failing sentences, then re-check what is left until nothing fails (removing a sentence can
            # leave a summary line that no longer has support).
            final, res.removed = _drop(draft, problems)
            for _ in range(3):
                left = verify(final, evidence)
                if not left:
                    break
                final, more = _drop(final, left)
                res.removed += more
            res.status = "trimmed"
            res.steps.append(_step("repair", "✂️", f"Removed {len(res.removed)} unverifiable statement(s)",
                                   "The rewrite did not pass the check, so the failing sentences were dropped "
                                   "and are never shown.", status="warn", ms=(time.time() - t) * 1000))

    if not _has_supported_claim(final, len(evidence)):
        res.status = "insufficient"
        res.text = REFUSAL + "\n\n" + INSUFFICIENT_DETAIL
        res.steps.append(_step("refuse", "⛔", "Declined: nothing verified", "No sentence survived the fact check.",
                               status="stop"))
        return res

    res.body = final
    if res.removed:
        final += f"\n\n_{len(res.removed)} statement(s) were removed because they could not be verified against the filings._"
    # Database facts (e.g. "showing 8 of 12 matching filings") are added by code, not left to the model, so a
    # partial list can never be presented as the complete one.
    for e in evidence:
        if e.doc is None and e.n not in _cites(final):
            final += f"\n\n_Note: {e.text.splitlines()[-1]} [{e.n}]_"
    res.text = final
    res.cited = sorted({c for c in _cites(final) if 1 <= c <= len(evidence)})
    res.steps.append(_step("cite", "📎", "Citation check",
                           f"{len(res.cited)} of {len(evidence)} passages cited; every [n] points to a real passage."))
    return res
