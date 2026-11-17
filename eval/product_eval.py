"""Product-level evaluation, adapted from MedEvolv Mentor's eval/product_eval.py.

    python eval/product_eval.py [--no-judge]

Per question: did the bot answer or decline as expected, are required facts present, did it avoid the trap words,
does the deterministic fact check pass on the final text, and (judge) what share of the answer's claims are
supported by the evidence it was given. The judge is an LLM of the same family as the answerer, so treat its score
as indicative, not ground truth. Writes eval/product_eval.json and eval/product_eval.md.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "chatbot"))
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import grounding  # noqa: E402
from agent import MarketTideAgent  # noqa: E402

JUDGE = """You check a financial-filings answer against the evidence it was given. Split the answer into its factual
claims. A claim is supported only if the evidence states it. Ignore refusals and statements that something is not
covered. Return JSON: {"claims": <int>, "supported": <int>, "unsupported": ["..."]}"""


def judge(client, res) -> dict | None:
    ev = "\n\n".join(e.text for e in res.evidence)
    try:
        # The judge runs on a different model than the answerer: it has its own per-minute quota on Groq, and a
        # second model family-member is a slightly more independent check.
        r = client.chat.completions.create(
            model="openai/gpt-oss-20b", temperature=0, max_tokens=1500, reasoning_effort="low",
            response_format={"type": "json_object"},
            messages=[{"role": "system", "content": JUDGE},
                      {"role": "user", "content": f"Evidence:\n{ev}\n\nAnswer:\n{res.text}"}])
        raw = r.choices[0].message.content or ""
        j = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
        n = max(int(j.get("claims", 0)), 1)
        return {"claims": n, "supported": min(int(j.get("supported", 0)), n), "unsupported": j.get("unsupported", [])[:5]}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:100]}"}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-judge", action="store_true")
    a = ap.parse_args()
    qs = [json.loads(l) for l in open(os.path.join(ROOT, "eval", "product_questions.jsonl"), encoding="utf-8") if l.strip()]
    agent = MarketTideAgent()
    rows = []
    for q in qs:
        t = time.time()
        gen, docs, ctx = agent.stream_response(q["question"], [], True)
        text = "".join(gen)
        res = agent.last_result
        status = "declined" if (res is None and not docs) or (res is not None and res.status == "insufficient") \
            or ("i don't know" in text.lower()) else "answered"
        if res is None and docs and "SEBI" in text:          # advice route: compliance notice + filings, no LLM
            status = "declined"
        ok_status = q["expect"] in ("any", status)
        low = text.lower()
        missing = [m for m in q.get("must_contain", []) if m.lower() not in low]
        traps = [m for m in q.get("must_not_contain", []) if m.lower() in low]
        # Re-check the verified answer body (system notes like "1 statement was removed" are not claims)
        check = grounding.verify(res.body, res.evidence) if (res is not None and status == "answered") else []
        row = {"id": q["id"], "type": q["type"], "question": q["question"], "expect": q["expect"], "status": status,
               "pipeline": res.status if res else ctx, "ok_status": ok_status, "missing": missing, "traps": traps,
               "check_problems": len(check), "cited": res.cited if res else [], "latency_s": round(time.time() - t, 2),
               "answer": text}
        if res is not None and status == "answered" and not a.no_judge and agent.client is not None:
            row["judge"] = judge(agent.client, res)
        row["pass"] = ok_status and not missing and not traps and not check and \
            not (row.get("judge") and row["judge"].get("unsupported"))
        rows.append(row)
        print(f"{'PASS' if row['pass'] else 'FAIL'}  [{q['id']}] {status:9} {row['pipeline']:22} {q['question'][:70]}"
              + (f"  missing={missing}" if missing else "") + (f"  TRAP={traps}" if traps else "")
              + (f"  judge={row['judge']}" if row.get("judge") and (row['judge'].get('unsupported') or row['judge'].get('error')) else ""))

    judged = [r["judge"] for r in rows if r.get("judge") and "claims" in r["judge"]]
    claims = sum(j["claims"] for j in judged)
    supported = sum(j["supported"] for j in judged)
    summary = {
        "questions": len(rows), "passed": sum(r["pass"] for r in rows),
        "behaviour_correct": sum(r["ok_status"] for r in rows),
        "trap_hits": sum(bool(r["traps"]) for r in rows),
        "fact_check_failures_shown": sum(r["check_problems"] > 0 for r in rows),
        "judge_claims_supported": f"{supported}/{claims}" if claims else "n/a",
        "avg_latency_s": round(sum(r["latency_s"] for r in rows) / len(rows), 2),
    }
    json.dump({"summary": summary, "rows": rows}, open(os.path.join(ROOT, "eval", "product_eval.json"), "w",
                                                    encoding="utf-8"), indent=1, ensure_ascii=False)
    md = ["# Product evaluation (zero-hallucination pipeline)", "",
          *(f"- **{k.replace('_', ' ')}**: {v}" for k, v in summary.items()), "",
          "| id | type | question | expected | got | pass |", "|---|---|---|---|---|---|"]
    md += [f"| {r['id']} | {r['type']} | {r['question']} | {r['expect']} | {r['status']} ({r['pipeline']}) | "
           f"{'✅' if r['pass'] else '❌'} |" for r in rows]
    open(os.path.join(ROOT, "eval", "product_eval.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
