"""Evaluation + ablation: how much does each technique actually help?

    python eval/run_eval.py            # writes eval/results.md and eval/results.json

Three systems are compared on the same questions:
  A. Baseline RAG   - plain vector search, top-8, no query understanding, never refuses
  B. + Hybrid       - vectors + BM25 fused with RRF (+ cross-encoder rerank if TIDEBOT_RERANK=1), no filters
  C. TideBot (full) - query understanding, metadata filters, routing, decomposition, fallbacks
"""
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "chatbot"))
import config  # noqa: E402
import llm  # noqa: E402
from rag import Engine  # noqa: E402

QS = json.loads((ROOT / "eval" / "questions.json").read_text(encoding="utf-8"))


def check(item, sources, status, answer=""):
    tick = [s["filing"]["ticker"] for s in sources]
    tags = [s["filing"]["tag"] for s in sources]
    dates = [s["filing"]["date"] for s in sources]
    ok_status = status == item["status"]
    if item["status"] != "answered":
        return {"retrieval": None, "status": ok_status, "pass": ok_status}
    r = True
    if item.get("tickers"):
        r &= all(t in tick for t in item["tickers"])
    if item.get("tags"):
        good = sum(t in item["tags"] for t in tags)
        r &= good >= item.get("min_sources", 1) and good >= 0.8 * max(len(tags), 1)
    if item.get("date"):
        r &= bool(dates) and all(d == item["date"] for d in dates)
    if item.get("min_sources") and not item.get("tags"):
        r &= len(sources) >= item["min_sources"]
    if item.get("answer_has") and answer and llm.available():
        r &= all(a.lower() in answer.lower() for a in item["answer_has"])
    return {"retrieval": r, "status": ok_status, "pass": r and ok_status}


def main():
    eng = Engine()
    store = eng.store
    rows = []
    for item in QS:
        q = item["q"]
        # A: baseline
        a_hits = store.search(q, hybrid=False, rerank=False)
        a = check(item, a_hits, "answered")
        # B: hybrid + rerank, no query understanding
        b_hits = store.search(q, hybrid=True, rerank=True)
        b = check(item, b_hits, "answered")
        # C: full system
        t = time.time()
        res = eng.answer(q, [], hybrid=True, rerank=True, decompose=True)
        c = check(item, res["sources"], res["status"], res.get("answer", ""))
        g = res.get("grounding") or {}
        rows.append({"q": q, "type": item["type"], "A": a["pass"], "B": b["pass"], "C": c["pass"],
                     "route": res["route"], "status": res["status"], "sources": len(res["sources"]),
                     "latency": round(time.time() - t, 2), "grounding": g, "answer": res.get("answer", "")})
        print(f"{'PASS' if c['pass'] else 'FAIL'}  A={a['pass']} B={b['pass']}  [{res['route']}] {q}")

    n = len(rows)
    score = {k: sum(r[k] for r in rows) for k in "ABC"}
    ans = [r for r in rows if r["grounding"].get("checked")]
    nums_total = sum(r["grounding"]["checked"] for r in ans)
    nums_ok = sum(r["grounding"]["found"] for r in ans)
    summary = {
        "questions": n, "baseline_vector_only": score["A"], "hybrid_rerank": score["B"], "tidebot_full": score["C"],
        "llm": llm.available(), "reranker": config.RERANK_ENABLED, "numbers_verified": f"{nums_ok}/{nums_total}" if nums_total else "n/a",
        "avg_latency_s": round(sum(r["latency"] for r in rows) / n, 2),
    }
    out = ["# Evaluation results", "",
           f"- Questions: **{n}**  ·  LLM connected: **{summary['llm']}**  ·  Reranker: **{config.RERANK_ENABLED}**",
           f"- A. Baseline (vector only): **{score['A']}/{n}**",
           f"- B. Hybrid search (no query understanding): **{score['B']}/{n}**",
           f"- C. TideBot full system: **{score['C']}/{n}**",
           f"- Numbers in answers found in sources: **{summary['numbers_verified']}**",
           f"- Average latency (full system): **{summary['avg_latency_s']}s**", "",
           "| # | Type | Question | A | B | C | Route | Status |", "|---|---|---|---|---|---|---|---|"]
    mark = {True: "✅", False: "❌"}
    for i, r in enumerate(rows, 1):
        out.append(f"| {i} | {r['type']} | {r['q']} | {mark[r['A']]} | {mark[r['B']]} | {mark[r['C']]} | "
                   f"{r['route']} | {r['status']} |")
    (ROOT / "eval" / "results.md").write_text("\n".join(out) + "\n", encoding="utf-8")
    (ROOT / "eval" / "results.json").write_text(json.dumps({"summary": summary, "rows": rows}, indent=1,
                                                           ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
