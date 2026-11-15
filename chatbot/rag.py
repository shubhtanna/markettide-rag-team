"""The RAG engine: question -> understand -> route -> retrieve -> generate -> verify.

Routes (chosen from the parsed question, not by the LLM, so they are fast and predictable):
  greeting / help      canned reply with example questions
  advice               polite refusal + the facts we do have (no buy/sell calls)
  live_price           we hold filings, not prices -> say so, show filings instead
  out_of_window        asked about dates we don't have -> say exactly what we cover
  list / top           "which companies announced a buyback?" -> metadata query over ALL
                       matching filings (top-k retrieval would silently miss some)
  compare / multi-part query decomposition: one retrieval per sub-question
  lookup               hybrid retrieval with metadata filters, relaxed step by step
"""
import re
import time

import config
import llm
from query_parser import FOLLOWUP, ParsedQuery, parse
from retriever import Store, tokenize

SYSTEM = """You are TideBot, an assistant that answers questions about Indian stock-exchange (NSE) corporate
filings published between {date_from} and {date_to}. The filings are given to you as numbered SOURCES.

Rules:
1. Use ONLY the SOURCES. Never add outside knowledge about companies, share prices or events.
2. End every factual sentence with its citation, e.g. [2] or [1][3]. Only cite numbers that exist.
3. Copy figures exactly as written (Rs, crore, lakh, %, per share, dates). Never calculate new figures
   unless the user asks, and then show the inputs you used.
4. If the SOURCES do not contain the answer, reply with exactly: NOT_FOUND
   If they answer only part of the question, answer that part and say clearly what is missing.
5. Never give buy / sell / hold advice, price targets or predictions.
6. Style: one short opening sentence, then bullet points. Company names in **bold**. Dates like "14 Nov".
   Keep it under 220 words unless the user asks for a list."""

DECOMPOSE = """Split the user's question about stock-exchange filings into 1-4 simple, self-contained search
questions that together answer it. Keep company names and dates in each sub-question.
Return JSON: {"sub_questions": ["...", "..."]}"""

WEEK_WORDS = {"monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "jan", "feb", "mar",
              "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec", "november", "october", "december",
              "usfda", "fda", "nse", "bse", "sebi", "nclt", "ceo", "cfo", "qip", "ipo"}

EXAMPLES = [
    "What did Ashok Leyland announce this week?",
    "Which companies declared a dividend this week?",
    "Compare the latest results of Bajaj Finserv and Committed Cargo Care",
    "Any buybacks or bonus issues in the last 3 days?",
    "What were the most important filings yesterday?",
    "Which companies won new orders and what was the order value?",
]


BOILERPLATE = re.compile(
    r"yours (faithfully|truly|sincerely)|thanking you|dear sir|for and on behalf|company secretary|"
    r"compliance officer|\bdin\b|membership no|\bsub(ject)?\s*:|\bref\s*:|scrip code|symbol\s*:|"
    r"listing (department|compliance)|phiroze|bandra.kurla|dalal street|kindly take|"
    r"take (the )?(above|same) on (your )?record|pursuant to regulation|whether the|if yes|nature of interest",
    re.I)
MONEY = re.compile(r"(rs\.?|inr|₹|\bcrore|\bcr\b|lakh|million|mn\b|billion|%|per (equity )?share)", re.I)


def _sentence_score(sentence, qtokens):
    toks = set(tokenize(sentence))
    return 2 * len(qtokens & toks) + (2 if MONEY.search(sentence) else 0) + (1 if re.search(r"\d", sentence) else 0)


def _fmt_date(d):
    import datetime as dt
    return dt.date.fromisoformat(d).strftime("%d %b")


class Engine:
    def __init__(self, store: Store | None = None):
        self.store = store or Store()
        m = self.store.manifest
        self.coverage = f"{_fmt_date(m['date_from'])} to {_fmt_date(m['date_to'])} {m['date_to'][:4]}"

    # ------------------------------------------------------------------ public
    def answer(self, question, history=None, hybrid=True, rerank=True, decompose=True, use_llm=True):
        t0 = time.time()
        s = self.store
        p = parse(question, s.companies, s.anchor, s.first)
        res = {"question": question, "parsed": p, "route": p.intent, "sources": [], "sub_questions": [],
               "notes": [], "model": None, "status": "answered", "grounding": None}

        # Follow-ups: "what about their dividend?" -> reuse the last company discussed.
        if not p.companies and history and FOLLOWUP.search(question):
            for turn in reversed(history):
                prev = turn.get("parsed")
                if prev and prev.companies:
                    p.companies = prev.companies
                    res["notes"].append("Follow-up: using " + ", ".join(c for c, _ in p.companies))
                    if p.intent in ("list", "top"):
                        p.intent = "lookup"
                    res["route"] = p.intent
                    break

        handler = {
            "greeting": self._greeting, "help": self._greeting, "advice": self._advice,
            "live_price": self._live_price, "list": self._list, "top": self._top,
            "compare": self._compare,
        }.get(p.intent, self._lookup)
        if p.out_of_window and p.intent not in ("greeting", "help", "advice"):
            handler = self._out_of_window
            res["route"] = "out_of_window"

        ctx = {"hybrid": hybrid, "rerank": rerank, "decompose": decompose,
               "use_llm": use_llm and llm.available(), "history": history or []}
        handler(p, res, ctx)
        res["latency"] = round(time.time() - t0, 2)
        return res

    # ------------------------------------------------------------------ routes
    def _greeting(self, p, res, ctx):
        m = self.store.manifest
        res["status"] = "info"
        res["answer"] = (
            f"Hi! I'm **TideBot**. I answer questions about **{m['filings']:,} NSE company filings** "
            f"from **{self.coverage}**, and every answer links to the original filing.\n\n"
            "Try asking:\n" + "\n".join(f"- {e}" for e in EXAMPLES) +
            f"\n\n_{config.DISCLAIMER}_")

    def _out_of_window(self, p, res, ctx):
        res["status"] = "out_of_window"
        res["answer"] = (f"I only have NSE filings from **{self.coverage}**, so I can't answer about "
                         f"{p.date_label or 'that period'}. Ask me about anything filed in that window.")

    def _live_price(self, p, res, ctx):
        res["status"] = "refused"
        msg = ("I work from company **filings**, not live market data, so I don't have share prices "
               "or market caps.")
        if p.companies:
            self._lookup(p, res, ctx, preface=msg + " Here is what the company filed recently:")
        else:
            res["answer"] = msg + " Ask me what a company announced instead."

    def _advice(self, p, res, ctx):
        res["status"] = "refused"
        msg = ("I can't tell you whether to buy, sell or hold a stock. That would be investment advice, "
               "and I only summarise public filings.")
        if p.companies:
            self._lookup(p, res, ctx, preface=msg + " Here are the facts from recent filings to help your own research:")
            res["status"] = "refused"
        else:
            res["answer"] = msg + f"\n\n_{config.DISCLAIMER}_"

    def _list(self, p, res, ctx):
        s = self.store
        if not p.tags:
            # "which companies talked about EVs?" has no category -> semantic search, wider net
            res["route"] = "list (semantic)"
            hits = s.search(p.text, p.date_from, p.date_to, None, None, ctx["hybrid"], ctx["rerank"], k=12)
            return self._generate(p, res, ctx, hits, list_mode=True)
        docs = s.list_filings(date_from=p.date_from, date_to=p.date_to, tags=p.tags)
        res["route"] = "list (metadata filter)"
        res["notes"].append(f"{len(docs)} filings match {', '.join(p.tags)}"
                            + (f" ({p.date_label})" if p.date_label else ""))
        if not docs:
            res["status"] = "not_found"
            res["answer"] = (f"No **{' / '.join(p.tags)}** filings found"
                             f"{' for ' + p.date_label if p.date_label else ' in ' + self.coverage}.")
            return
        hits = [self._doc_hit(d) for d in docs[:config.LIST_LIMIT]]
        self._generate(p, res, ctx, hits, list_mode=True, total=len(docs))

    def _top(self, p, res, ctx):
        s = self.store
        df, dt_ = p.date_from, p.date_to
        if not df:
            df = dt_ = s.anchor.isoformat()
            if not s.filter_docs(df, dt_):
                df = s.first.isoformat()
            res["notes"].append("No date given: using the latest day in the data")
        docs = s.list_filings(date_from=df, date_to=dt_, tags=p.tags or None)
        # Routine results and call transcripts flood the top; prefer distinctive events.
        routine = {"Results", "Concall", "Investor Meet", "Outcome", "Investor Presentation"}
        special = [d for d in docs if s.filings[d]["tag"] not in routine]
        docs = (special + [d for d in docs if d not in set(special)])[:12] if not p.tags else docs[:12]
        res["route"] = "top (ranked by importance score)"
        hits = [self._doc_hit(d) for d in docs]
        self._generate(p, res, ctx, hits, list_mode=True, total=len(docs))

    def _compare(self, p, res, ctx):
        subs = []
        if ctx["decompose"] and ctx["use_llm"]:
            try:
                out, _ = llm.chat_json([{"role": "system", "content": DECOMPOSE},
                                        {"role": "user", "content": p.text}])
                subs = [q for q in out.get("sub_questions", []) if isinstance(q, str)][:4]
            except Exception:
                subs = []
        if not subs and p.companies:
            name_words = {w for c, t in p.companies for w in (c + " " + t).lower().split()}
            topic = [w for w in re.findall(r"[A-Za-z0-9']+", p.text)
                     if w.lower() not in name_words and w.lower() not in
                     {"compare", "comparison", "versus", "vs", "and", "between", "the", "of", "with", "to"}]
            subs = [f"{c}: {' '.join(topic)}".strip() for c, _ in p.companies]
        if not subs:
            return self._lookup(p, res, ctx)
        res["sub_questions"] = subs
        res["route"] = "compare (query decomposition)"
        hits, seen = [], set()
        for q in subs:
            sp = parse(q, self.store.companies, self.store.anchor, self.store.first)
            comps = sp.companies or None
            got = self.store.search(q, p.date_from, p.date_to, comps, None, ctx["hybrid"], ctx["rerank"], k=4)
            if not got and comps:
                got = self.store.search(q, None, None, comps, None, ctx["hybrid"], ctx["rerank"], k=4)
            for h in got:
                if h["chunk_id"] not in seen:
                    seen.add(h["chunk_id"])
                    hits.append(h)
        self._generate(p, res, ctx, hits)

    def _lookup(self, p, res, ctx, preface=None):
        s = self.store
        # Filters are hard constraints, relaxed one at a time if they return nothing.
        # Company is never relaxed: answering about the wrong company is worse than "not found".
        tries = [(p.date_from, p.date_to, p.tags, None)]
        if p.tags:
            tries.append((p.date_from, p.date_to, None, "no exact category match, searched all categories"))
        if p.date_from:
            tries.append((None, None, None, f"nothing on {p.date_label}, searched the whole week"))
        hits = []
        for df, dt_, tags, note in tries:
            hits = s.search(p.text, df, dt_, p.companies or None, tags or None, ctx["hybrid"], ctx["rerank"])
            if hits:
                if note:
                    res["notes"].append(note)
                break
        unknown = self._unknown_names(p)
        if unknown and not p.companies:
            res["status"] = "not_found"
            res["answer"] = (f"I have no filings that mention **{', '.join(unknown)}** in {self.coverage}. "
                             "It may not be listed on NSE, or it filed nothing this week.")
            return
        if not p.companies and not p.tags and not p.date_from:
            best = s.best_dense(p.text)
            res["best_similarity"] = round(best, 3)
            if best < config.MIN_DENSE_SCORE:
                res["status"] = "not_found"
                res["answer"] = (config.NOT_FOUND +
                                 " Your question doesn't match any filing closely enough "
                                 f"(best match {best:.2f}). I cover NSE filings from {self.coverage}.")
                res["sources"] = hits[:3]
                return
        if p.companies and not hits:
            res["status"] = "not_found"
            names = ", ".join(c for c, _ in p.companies)
            res["answer"] = f"I found no filings from **{names}** in {self.coverage}."
            return
        self._generate(p, res, ctx, hits, preface=preface)

    def _unknown_names(self, p):
        """Capitalised names in the question that appear nowhere in the data ("Tesla").
        Vector search would happily return the 'closest' unrelated filing for these."""
        from query_parser import COMMON_WORDS
        vocab = self.store.bm25.idf
        words = re.findall(r"\b[A-Z][A-Za-z0-9&]{2,}\b", p.text)
        first = p.text.split()[0] if p.text.split() else ""
        out = []
        for w in words:
            lw = w.lower()
            if w == first or lw in COMMON_WORDS or lw in vocab or lw in WEEK_WORDS:
                continue
            out.append(w)
        return out

    # ------------------------------------------------------------------ generation
    def _doc_hit(self, d):
        f = self.store.filings[d]
        cids = self.store.doc_chunks.get(d, [])
        text = self.store.chunks[cids[0]]["text"] if cids else f["headline"]
        return {"chunk_id": cids[0] if cids else -1, "doc": d, "text": text, "filing": f}

    def _context(self, hits, list_mode):
        blocks = []
        for i, h in enumerate(hits, 1):
            f = h["filing"]
            body = h["text"].split("\n", 2)[-1] if "\n" in h["text"] else ""
            limit = 450 if list_mode else 1400
            blocks.append(f"[{i}] {f['company']} ({f['ticker']}) | {f['date']} {f['time']} | {f['tag']} | "
                          f"{f['category']}\nHeadline: {f['headline']}\nExcerpt: {body[:limit]}")
        return "\n\n".join(blocks)

    def _generate(self, p, res, ctx, hits, list_mode=False, total=None, preface=None):
        res["sources"] = hits
        if not hits:
            res["status"] = "not_found"
            res["answer"] = config.NOT_FOUND
            return
        if not ctx["use_llm"]:
            res["answer"] = (preface + "\n\n" if preface else "") + self._extractive(p, hits, list_mode, total)
            res["model"] = "extractive (no LLM key)"
            return

        m = self.store.manifest
        extra = []
        if total and total > len(hits):
            extra.append(f"There are {total} matching filings in total; you are shown the {len(hits)} most important. "
                         "Mention the total.")
        if p.date_label:
            extra.append(f"The user asked about: {p.date_label}.")
        if res["notes"]:
            extra.append("Retrieval notes: " + "; ".join(res["notes"]))
        hist = [t for t in ctx["history"][-2:] if t.get("answer")]
        convo = "".join(f"Earlier question: {t['question']}\n" for t in hist)
        user = (f"SOURCES:\n{self._context(hits, list_mode)}\n\n{convo}"
                f"{' '.join(extra)}\nQUESTION: {p.text}")
        msgs = [{"role": "system", "content": SYSTEM.format(date_from=m["date_from"], date_to=m["date_to"])},
                {"role": "user", "content": user}]
        try:
            text, model = llm.chat(msgs, max_tokens=1100 if list_mode else 800)
        except llm.LLMUnavailable as e:
            res["notes"].append(f"LLM unavailable ({str(e)[:80]}), showing evidence instead")
            res["answer"] = (preface + "\n\n" if preface else "") + self._extractive(p, hits, list_mode, total)
            res["model"] = "extractive (LLM error)"
            return
        res["model"] = model
        text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
        if text.strip().upper().startswith("NOT_FOUND"):
            res["status"] = "not_found"
            res["answer"] = (preface + "\n\n" if preface else "") + config.NOT_FOUND + \
                " The closest filings I found are listed under Sources."
            return
        text = self._clean_citations(text, len(hits))
        res["grounding"] = self._grounding(text, hits)
        res["answer"] = (preface + "\n\n" if preface else "") + text

    @staticmethod
    def _clean_citations(text, n):
        return re.sub(r"\[(\d+)\]", lambda m: m.group(0) if 1 <= int(m.group(1)) <= n else "", text)

    @staticmethod
    def _grounding(answer, hits):
        """Faithfulness check: every number in the answer must appear in the sources."""
        ctx = " ".join(h["text"] + " " + h["filing"]["headline"] + " " + h["filing"]["date"] for h in hits)
        ctx_n = re.sub(r"(?<=\d),(?=\d)", "", ctx)
        body = re.sub(r"\[\d+\]", "", answer)
        nums = set(re.findall(r"\d+(?:,\d+)*(?:\.\d+)?", body))
        nums = {x for x in nums if len(x.replace(",", "")) >= 2}
        if not nums:
            return {"checked": 0, "found": 0, "missing": []}
        missing = [x for x in nums if x.replace(",", "") not in ctx_n]
        # day numbers like "14" in "14 Nov" are dates, always present via the date field
        return {"checked": len(nums), "found": len(nums) - len(missing), "missing": sorted(missing)[:6]}

    def _extractive(self, p, hits, list_mode, total):
        q = set(tokenize(p.text))
        if list_mode:
            head = f"Found **{total or len(hits)}** matching filings" + (" (showing the top ones)" if total and total > len(hits) else "") + ":\n\n"
            rows = [f"- **{h['filing']['company']}** ({_fmt_date(h['filing']['date'])}, {h['filing']['tag']}): "
                    f"{h['filing']['headline'][:220]} [{i}]" for i, h in enumerate(hits, 1)]
            return head + "\n".join(rows)
        out = ["Here is what the filings say (direct extracts, because no LLM answer was available):\n"]
        for i, h in enumerate(hits[:4], 1):
            f = h["filing"]
            body = "\n".join(ln for ln in h["text"].split("\n")[1:] if not ln.startswith("Headline:"))
            sents = [x.strip() for x in re.split(r"(?<=[.;])\s+|\n", body) if len(x.strip()) > 25]
            sents = [x for x in sents if not BOILERPLATE.search(x)]
            ranked = sorted(range(len(sents)), key=lambda j: -_sentence_score(sents[j], q))[:2]
            snippet = " ".join(sents[j] for j in sorted(ranked))[:420]
            out.append(f"- **{f['company']}**, {_fmt_date(f['date'])} ({f['tag']}): {f['headline'][:200]}"
                       + (f"\n  > {snippet}" if snippet and snippet not in f["headline"] else "") + f" [{i}]")
        return "\n".join(out)
