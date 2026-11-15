"""Step 4: Streamlit chat UI.

    streamlit run chatbot/app.py
"""
import html
import pathlib
import sys

import streamlit as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import config  # noqa: E402
import llm  # noqa: E402
from embedder import warm_up  # noqa: E402
from rag import EXAMPLES, Engine, _fmt_date  # noqa: E402

st.set_page_config(page_title="TideBot · Market Tide", page_icon="🌊", layout="wide")

st.markdown("""
<style>
  .block-container {padding-top: 1.6rem; max-width: 1100px;}
  .tb-hero h1 {font-size: 2.1rem; margin-bottom: 0;}
  .tb-hero p {opacity: .75; margin-top: .2rem;}
  .tb-src {border: 1px solid rgba(128,128,128,.25); border-radius: 10px; padding: .6rem .8rem; margin-bottom: .5rem;}
  .tb-src b {font-size: .95rem;}
  .tb-meta {font-size: .78rem; opacity: .7;}
  .tb-pill {display:inline-block; font-size:.72rem; padding:1px 8px; border-radius:999px; margin-right:4px;
            background: rgba(99,102,241,.12); color: #6366f1; border: 1px solid rgba(99,102,241,.3);}
  .tb-ok {background: rgba(16,185,129,.12); color:#059669; border-color: rgba(16,185,129,.35);}
  .tb-warn {background: rgba(245,158,11,.12); color:#b45309; border-color: rgba(245,158,11,.35);}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading 7 days of filings and the search index...")
def get_engine():
    eng = Engine()
    warm_up(rerank=True)
    return eng


engine = get_engine()
m = engine.store.manifest

# ------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown("### 🌊 TideBot")
    st.caption(f"**{m['filings']:,}** NSE filings · **{m['chunks']:,}** chunks\n\n"
               f"Data: **{engine.coverage}**")
    st.divider()
    st.markdown("**Retrieval settings**")
    hybrid = st.toggle("Hybrid search (vectors + BM25)", value=True,
                       help="Off = vector search only. Turn it off to see why exact names need keyword search.")
    rerank = st.toggle("Cross-encoder reranking", value=True,
                       help="Re-scores the top 24 chunks by reading question and chunk together.")
    decompose = st.toggle("Query decomposition", value=True,
                          help="Splits comparison / multi-part questions into sub-questions.")
    show_trace = st.toggle("Show retrieval trace", value=True)
    st.divider()
    if llm.available():
        st.success("LLM connected", icon="✅")
    else:
        st.warning("No LLM key: answers are direct extracts from filings. Add GROQ_API_KEY to enable "
                   "generated answers.", icon="🔑")
    if st.button("Clear chat", use_container_width=True):
        st.session_state.history = []
        st.rerun()
    st.caption(config.DISCLAIMER)

# ------------------------------------------------------------------ header
st.markdown(f"""<div class="tb-hero"><h1>Ask the week's filings anything</h1>
<p>Answers come only from {m['filings']:,} NSE company filings ({engine.coverage}), each with a link to the original PDF.</p></div>""",
            unsafe_allow_html=True)

if "history" not in st.session_state:
    st.session_state.history = []


def render_sources(res):
    hits = res.get("sources") or []
    if not hits:
        return
    with st.expander(f"📄 Sources ({len(hits)})", expanded=False):
        for i, h in enumerate(hits, 1):
            f = {k: html.escape(str(v)) for k, v in h["filing"].items()}
            link = f["pdf_url"] or f["page_url"]
            scores = []
            if "dense" in h:
                scores.append(f"vector {h['dense']:.2f}")
            if "bm25" in h:
                scores.append(f"BM25 {h['bm25']:.1f}")
            if "rerank" in h:
                scores.append(f"rerank {h['rerank']:.2f}")
            excerpt = html.escape(h["text"].split("\n", 2)[-1][:420]) if "\n" in h["text"] else ""
            st.markdown(
                f"<div class='tb-src'><b>[{i}] {f['company']}</b> <span class='tb-pill'>{f['tag']}</span>"
                f"<div class='tb-meta'>{_fmt_date(h['filing']['date'])} {f['time']} · {f['category']}"
                f"{' · ' + ' · '.join(scores) if scores else ''}</div>"
                f"<div style='font-size:.86rem;margin-top:.3rem'>{f['headline'][:300]}</div>"
                + (f"<div class='tb-meta' style='margin-top:.3rem'>{excerpt}…</div>" if excerpt else "")
                + (f"<div style='margin-top:.3rem'><a href='{link}' target='_blank'>Open original filing ↗</a></div>" if link else "")
                + "</div>", unsafe_allow_html=True)


def render_trace(res):
    p = res["parsed"]
    with st.expander("🔍 How I found this", expanded=False):
        cols = st.columns(4)
        cols[0].metric("Route", res["route"].split(" (")[0])
        cols[1].metric("Sources", len(res.get("sources") or []))
        cols[2].metric("Time", f"{res.get('latency', 0)}s")
        g = res.get("grounding")
        cols[3].metric("Numbers verified", f"{g['found']}/{g['checked']}" if g and g["checked"] else "—")
        rows = {
            "Route detail": res["route"],
            "Companies detected": ", ".join(f"{c} ({t})" for c, t in p.companies) or "—",
            "Date filter": f"{p.date_label} ({p.date_from} → {p.date_to})" if p.date_from else (p.date_label or "whole week"),
            "Category filter": ", ".join(p.tags) or "—",
            "Sub-questions": " | ".join(res.get("sub_questions") or []) or "—",
            "Notes": " · ".join(res.get("notes") or []) or "—",
            "Model": res.get("model") or "—",
        }
        if "best_similarity" in res:
            rows["Best vector similarity"] = res["best_similarity"]
        if g and g.get("missing"):
            rows["Numbers not found in sources"] = ", ".join(g["missing"])
        st.table({"": list(rows.keys()), "value": [str(v) for v in rows.values()]})


def render_badges(res):
    pills = []
    status = res.get("status")
    if status == "not_found":
        pills.append("<span class='tb-pill tb-warn'>not in data</span>")
    elif status == "refused":
        pills.append("<span class='tb-pill tb-warn'>no advice</span>")
    elif status == "out_of_window":
        pills.append("<span class='tb-pill tb-warn'>outside data window</span>")
    g = res.get("grounding")
    if g and g["checked"]:
        cls = "tb-ok" if g["found"] == g["checked"] else "tb-warn"
        pills.append(f"<span class='tb-pill {cls}'>{g['found']}/{g['checked']} numbers verified in sources</span>")
    if res.get("sources"):
        pills.append(f"<span class='tb-pill'>{len(res['sources'])} sources</span>")
    if pills:
        st.markdown(" ".join(pills), unsafe_allow_html=True)


def show(res):
    st.markdown(res["answer"])
    render_badges(res)
    render_sources(res)
    if show_trace and res["route"] not in ("greeting", "help"):
        render_trace(res)


for turn in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(turn["question"])
    with st.chat_message("assistant", avatar="🌊"):
        show(turn)

pending = None
if not st.session_state.history:
    st.markdown("**Try one of these:**")
    cols = st.columns(2)
    for i, ex in enumerate(EXAMPLES):
        if cols[i % 2].button(ex, key=f"ex{i}", use_container_width=True):
            pending = ex

typed = st.chat_input("Ask about any NSE filing from the last 7 days…")
question = typed or pending
if question:
    with st.chat_message("user"):
        st.markdown(question)
    with st.chat_message("assistant", avatar="🌊"):
        with st.spinner("Searching filings…"):
            res = engine.answer(question, st.session_state.history, hybrid=hybrid, rerank=rerank,
                                decompose=decompose)
        show(res)
    st.session_state.history.append(res)
