"""
app.py - Market Tide "Spatial Financial Intelligence" chatbot, running on Streamlit.

    streamlit run chatbot/app.py

The UI is the original Spatial Financial Intelligence page (chatbot/spatial_ui/index.html), served unchanged as a
Streamlit custom component and shown full-screen. When the user searches, the page sends the question to this
Python script; the script answers it with the RAG pipeline and sends the result back to the page:

    question -> MarketTideAgent: guard rails, routing, hybrid retrieval (BM25 + vectors, RRF)
             -> grounding.answer: numbered evidence -> temperature-0 draft that must cite every claim
                -> deterministic fact check (citations, numbers, companies) -> repair or drop -> decline if nothing
                   verified remains
             -> page: verified answer in the synthesis card, the evidence filings in the table ([n] = row n)
"""

import math
import os
import re
import sys

import streamlit as st
import streamlit.components.v1 as components

# Windows consoles default to cp1252, which crashes on the "✓" progress prints. Force UTF-8 output.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

from agent import MarketTideAgent  # noqa: E402


def should_show_sources(text: str, sources: list, tool_context: str) -> bool:
    """Strict gate: Only display source dossiers when genuine matching documents exist."""
    if not sources or len(sources) == 0:
        return False

    text_lower = (text or "").lower()
    if "i don't know" in text_lower or "i dont know" in text_lower:
        return False

    tool_ctx = (tool_context or "").strip().lower()
    suppressed_contexts = {"out_of_domain", "greeting", "no_matches", "non_nse", "out_of_window", "zero_filing", "subjective_opinion"}
    if (
        tool_ctx in suppressed_contexts or
        tool_ctx.startswith("out_of_domain") or
        tool_ctx.startswith("greeting") or
        tool_ctx.startswith("no_matches") or
        tool_ctx.startswith("non_nse") or
        tool_ctx.startswith("out_of_window") or
        tool_ctx.startswith("subjective_opinion")
    ):
        return False

    negative_substrings = [
        "i don't know", "i dont know",
        "not present in the 7-day", "not present in the database", "not present in our database",
        "outside my scope", "outside the scope", "outside our scope", "falls outside",
        "no announcement matching this criteria was published", "no matching filings found",
        "no matching announcements were published", "no announcements were published by",
        "no corporate announcements found", "no corporate announcements",
        "zero official filings were published", "zero official filings",
        "not listed on the nse", "not listed on nse",
        "refusal", "query rejection", "scope refusal",
        "factual disclosures rather than subjective opinions", "subjective opinions",
        "cannot answer questions about", "cannot provide information derived from",
        "i am sorry, but i cannot answer", "i'm sorry, but i cannot answer",
        "i am sorry, but i can only provide analysis", "i'm sorry, but i can only provide analysis"
    ]
    if any(s in text_lower for s in negative_substrings):
        return False

    refusal_patterns = [
        r'\brefusal\b',
        r'\bquery\s+rejection\b',
        r'\bscope\s+refusal\b',
        r'\bdomain\s+(?:boundary\s+)?(?:scope\s+)?(?:refusal|notice)\b',
        r'\bmarket\s+scope\s+notice\b',
        r'\bdataset\s+window\s+notice\b',
        r'outside\s+(?:the\s+|our\s+)?(?:operational\s+)?(?:boundary|scope)\b',
        r'falls\s+outside\s+(?:the\s+|our\s+)?(?:scope|domain|operational)\b',
        r'cannot\s+answer\s+(?:questions\s+about\s+)?(?:sports|celebrities|cricket|entertainment|general|trivia|coding|recipes|weather)\b',
        r'cannot\s+provide\s+information\s+derived\s+from\s+nse\s+filings\b',
        r'i(?:\u2019|\')m\s+sorry,\s+but\s+i\s+can(?:\u2019|\')t\s+answer\b',
        r'i\s+am\s+sorry,\s+but\s+i\s+cannot\s+answer\b',
        r'\bno\s+matching\s+filings\s+found\b',
        r'\bno\s+official\s+corporate\s+filings\b',
        r'\bthere\s+are\s+no\s+(?:filings|announcements)\b',
        r'\bnone\s+from\s+[a-z0-9\s]+\b',
        r'\bnot\s+archived\s+in\s+this\s+assignment\b'
    ]
    if any(re.search(pat, text_lower) for pat in refusal_patterns):
        return False

    return True


# ---------------------------------------------------------------- answer -> page data

REFUSAL_TITLES = {
    "out_of_domain": "Outside Operational Scope",
    "subjective_opinion": "Outside Operational Scope",
    "non_nse": "Not an NSE-Listed Entity",
    "out_of_window": "Outside the 7-Day Window",
    "greeting": "Market Tide Terminal",
}


def _plain(text: str) -> str:
    """The page shows the summary as plain text: turn the answer's light markdown into readable lines."""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", text or "")
    t = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", t)
    t = re.sub(r"^\s*[-*]\s+", "• ", t, flags=re.M)
    t = re.sub(r"^#+\s*", "", t, flags=re.M)
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def _val(v, default=""):
    if v is None:
        return default
    if isinstance(v, float) and math.isnan(v):
        return default
    s = str(v).strip()
    return default if s.lower() in {"nan", "none"} else s


def _row(doc: dict, excerpt: str = "") -> dict:
    """One filing in the format the page's table already renders."""
    score = doc.get("importance_score")
    try:
        score = int(float(score))
    except (TypeError, ValueError):
        score = "--"
    return {
        "id": _val(doc.get("id")), "date": _val(doc.get("date")), "time": _val(doc.get("time")),
        "ticker": _val(doc.get("ticker")), "company": _val(doc.get("company")),
        "tag": _val(doc.get("tag")), "category": _val(doc.get("category")),
        "headline": _val(doc.get("headline")),
        # The drawer shows the exact filing text the answer was checked against (or the filing's own description).
        "description": excerpt or _val(doc.get("description")) or _val(doc.get("headline")),
        "pdf_url": _val(doc.get("pdf_url"), "#"), "importance_score": score,
    }


def answer_for_page(agent: MarketTideAgent, query: str) -> dict:
    gen, docs, tool_context = agent.stream_response(query, [], True)
    text = "".join(gen)
    result = agent.last_result
    ctx = (tool_context or "").split(":")[0]

    declined = (result is not None and result.status == "insufficient") or not should_show_sources(text, docs, tool_context)
    if declined:
        return {
            "query": query, "totalMatches": 0, "results": [],
            "synthesis": {"title": REFUSAL_TITLES.get(ctx, "No Statutory Disclosures Located"),
                          "summary": _plain(text), "highlights": [], "entitiesCount": 0, "avgImportance": "--"},
        }

    excerpts = {}
    if result is not None:
        for e in result.evidence:
            if e.doc is not None:
                m = re.search(r"Filing text excerpt: (.*)", e.text, re.S)
                ex = m.group(1).strip() if m else ""
                excerpts[_val(e.doc.get("id"))] = "" if ex.startswith("(not available") else ex
    rows = [_row(d, excerpts.get(_val(d.get("id")), "")) for d in docs]
    scores = [r["importance_score"] for r in rows if isinstance(r["importance_score"], int)]
    status = result.status if result is not None else ""
    title = {"answered": "Verified Regulatory Synthesis", "repaired": "Verified Regulatory Synthesis",
             "trimmed": "Verified Regulatory Synthesis (unverifiable lines removed)",
             "no_llm": "Filing Headlines (no language model key)"}.get(status, "Regulatory Disclosures")
    return {
        "query": query, "totalMatches": len(rows), "results": rows,
        "matchedTicker": rows[0]["ticker"] if len(rows) == 1 else None,
        "synthesis": {"title": title, "summary": _plain(text), "highlights": [],
                      "entitiesCount": len({r["ticker"] for r in rows}),
                      "avgImportance": round(sum(scores) / len(scores)) if scores else "--"},
    }


# ---------------------------------------------------------------- Streamlit page

def main() -> None:
    st.set_page_config(page_title="MarketTide AI — Spatial Financial Intelligence", page_icon="📈",
                       layout="wide", initial_sidebar_state="collapsed")
    # Full-bleed: hide Streamlit's own chrome so the Spatial page fills the window exactly as designed.
    st.markdown("""
    <style>
      header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
      [data-testid="stStatusWidget"], footer, #MainMenu { display: none !important; }
      html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stMain"] { background: #050914 !important; }
      .block-container, [data-testid="stMainBlockContainer"] { padding: 0 !important; max-width: 100% !important; }
      [data-testid="stVerticalBlock"] { gap: 0 !important; }
      iframe { display: block; border: 0; width: 100% !important; }
    </style>
    """, unsafe_allow_html=True)

    @st.cache_resource(show_spinner="Loading the 2,766-filing index…")
    def load_agent():
        return MarketTideAgent()

    @st.cache_resource
    def load_component():
        return components.declare_component("spatial_terminal", path=os.path.join(CURRENT_DIR, "spatial_ui"))

    agent = load_agent()
    terminal = load_component()

    request = terminal(response=st.session_state.get("response"), key="spatial_terminal", default=None)
    if request and request.get("nonce") and request.get("nonce") != st.session_state.get("answered_nonce"):
        st.session_state["answered_nonce"] = request["nonce"]
        query = str(request.get("query", "")).strip()[:500]
        data = answer_for_page(agent, query) if query else {"query": "", "totalMatches": 0, "results": [],
                                                              "synthesis": {"title": "Empty query", "summary": ""}}
        st.session_state["response"] = {"nonce": request["nonce"], "data": data}
        st.rerun()


if __name__ == "__main__":
    main()
