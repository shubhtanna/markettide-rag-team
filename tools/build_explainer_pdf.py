"""Builds docs/3_TideBot_How_We_Built_It.pdf from the code's real numbers.

    python tools/build_explainer_pdf.py
Reads chatbot/index/manifest.json and eval/results.json, so re-run after re-indexing / re-evaluating.
"""
import json
import pathlib
import sys

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFontFamily
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "chatbot"))
import config  # noqa: E402

man = json.loads((ROOT / "chatbot" / "index" / "manifest.json").read_text(encoding="utf-8"))
ev = json.loads((ROOT / "eval" / "results.json").read_text(encoding="utf-8"))
S = ev["summary"]
N = S["questions"]

F = "C:/Windows/Fonts/"
for name, file in (("Body", "arial.ttf"), ("BodyB", "arialbd.ttf"), ("BodyI", "ariali.ttf"), ("Mono", "consola.ttf")):
    pdfmetrics.registerFont(TTFont(name, F + file))
registerFontFamily("Body", normal="Body", bold="BodyB", italic="BodyI", boldItalic="BodyB")

NAVY, TEAL, LIGHT, GREY = (colors.HexColor(c) for c in ("#14325c", "#0f7c86", "#eef4f8", "#5b6670"))
H1 = ParagraphStyle("h1", fontName="BodyB", fontSize=20, leading=24, textColor=NAVY, spaceAfter=2)
SUB = ParagraphStyle("sub", fontName="Body", fontSize=10.5, leading=14, textColor=GREY, spaceAfter=8)
H2 = ParagraphStyle("h2", fontName="BodyB", fontSize=13, leading=16, textColor=TEAL, spaceBefore=9, spaceAfter=4)
H3 = ParagraphStyle("h3", fontName="BodyB", fontSize=10.3, leading=13, textColor=NAVY, spaceBefore=4, spaceAfter=2)
P = ParagraphStyle("p", fontName="Body", fontSize=9.4, leading=12.9, spaceAfter=4)
B = ParagraphStyle("b", parent=P, leftIndent=12, bulletIndent=2, spaceAfter=2)
CELL = ParagraphStyle("cell", fontName="Body", fontSize=8.5, leading=10.8)
CELLB = ParagraphStyle("cellb", parent=CELL, fontName="BodyB", textColor=colors.white)
CODE = ParagraphStyle("code", fontName="Mono", fontSize=8.1, leading=10.4, backColor=LIGHT, borderPadding=6,
                      leftIndent=6, rightIndent=6, spaceBefore=4, spaceAfter=8)
NOTE = ParagraphStyle("note", parent=P, backColor=colors.HexColor("#fff6e0"), borderPadding=6, leftIndent=6,
                      rightIndent=6, spaceBefore=4, spaceAfter=8)
W = A4[0] - 36 * mm


def bl(items):
    return [Paragraph(t, B, bulletText="\u2022") for t in items]


def table(rows, widths, head=True):
    data = [[Paragraph(str(c), CELLB if head and i == 0 else CELL) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c9d3dc")), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
        st += [("BACKGROUND", (0, i), (-1, i), LIGHT) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st))
    return t


def code(t):
    return Paragraph(t.replace("&", "&amp;").replace("<", "&lt;").replace(" ", "&nbsp;").replace("\n", "<br/>"), CODE)


def pct(a):
    return f"{a}/{N} ({round(100 * a / N)}%)"


s = []
s += [Paragraph("TideBot: How We Built It and Why", H1),
      Paragraph("A RAG chatbot over the last 7 days of NSE company filings. This document explains every design "
                "decision, the reasoning behind it, and the measured results.", SUB)]

s += [Paragraph("1. The one-minute version", H2),
      Paragraph(f"TideBot answers questions about <b>{man['filings']:,} NSE corporate filings</b> from "
                f"<b>{man['date_from']} to {man['date_to']}</b>. Each filing's original PDF was downloaded and its text "
                f"added to the data ({man['with_pdf_text']:,} filings have PDF text), then split into "
                f"<b>{man['chunks']:,} chunks</b>. A question goes through <b>query understanding</b> "
                "(company, date, category, intent), then a <b>route</b>, <b>hybrid retrieval</b> (FAISS vectors + BM25, "
                "fused with RRF, optional cross-encoder rerank), a grounded <b>LLM answer with citations</b>, and an "
                "automatic <b>number check</b> against the sources.", P),
      Paragraph(f"<b>Result on our {N}-question test set:</b> plain vector RAG passes {pct(S['baseline_vector_only'])}, "
                f"hybrid search alone {pct(S['hybrid_rerank'])}, the full TideBot {pct(S['tidebot_full'])}. "
                "The gain comes from understanding the question <i>before</i> searching.", NOTE)]

s += [Paragraph("2. Architecture", H2),
      code("CSV (NSE filings, 7 days) --+-- PDF text download (tools/enrich_pdf_text.py)\n"
           "                            |\n"
           "ingest.py:  clean -> contextual chunks -> bge-small embeddings -> FAISS index (+ BM25 at load)\n"
           "                            |\n"
           "question -> query_parser.py: companies | dates | categories | intent\n"
           "         -> rag.py router:\n"
           "              greeting/help | advice -> refuse + facts | live price -> explain\n"
           "              out-of-window | unknown company | off-topic -> honest 'not in data'\n"
           "              list / top   -> metadata query over ALL matching filings\n"
           "              compare      -> query decomposition -> one retrieval per sub-question\n"
           "              lookup       -> filtered hybrid retrieval (relaxed step by step)\n"
           "         -> retriever.py: filter -> FAISS + BM25 -> RRF -> diversity -> cross-encoder rerank\n"
           "         -> llm.py: Groq (3 models) -> Gemini -> extractive fallback\n"
           "         -> verify citations + numbers -> app.py (Streamlit: answer, sources, trace)"),
      table([
          ["File", "Job"],
          ["tools/enrich_pdf_text.py", "Downloads each filing's PDF, keeps the first 6 pages of text, removes address/contact noise"],
          ["chatbot/ingest.py", "Cleans data, builds chunks, embeds them, writes the FAISS index"],
          ["chatbot/query_parser.py", "Finds companies, dates, categories and intent in the question"],
          ["chatbot/retriever.py", "Metadata filtering, FAISS + BM25 hybrid search, RRF, reranking"],
          ["chatbot/rag.py", "Routing, decomposition, prompt, fallbacks, grounding check"],
          ["chatbot/llm.py", "Groq / Gemini calls with automatic fallback"],
          ["chatbot/app.py", "Streamlit UI"],
          ["eval/run_eval.py", "Test set, ablation (A/B/C) and results table"],
      ], [45 * mm, W - 45 * mm])]

s += [Paragraph("3. Data: why we added the PDF text", H2),
      Paragraph("The exchange feed gives only a headline such as <i>\"has submitted financial results for the period "
                "ended September 30\"</i>. That is useless for questions like <i>\"what was the order value?\"</i>. "
                "The facts live inside the PDF, so we download every filing and keep the first 6 pages "
                "(facts are almost always on page 1-2; the tail is annexures). Lines with addresses, CIN, e-mail and "
                "phone numbers are removed because they match every query and add noise.", P)]
s += bl(["<b>Cleaning:</b> empty headlines dropped, duplicate IDs dropped, same company + same day + same headline "
         "merged, routine paperwork already filtered by Market Tide's importance score (kept score &ge; 45).",
         "<b>Source &amp; honesty:</b> public NSE disclosures only. BSE refused automated requests during export, "
         "so it is not included, and we say so in the README.",
         f"<b>Coverage:</b> {man['filings']:,} filings, {man['with_pdf_text']:,} with PDF text, "
         "35 categories (Results, Dividend, Buyback, Order, Acquisition, Ratings ...)."])

s += [Paragraph("4. Chunking, embeddings and vector store", H2),
      table([
          ["Choice", "What we did", "Why"],
          ["Chunk size", f"{config.CHUNK_WORDS} words (~240 tokens), {config.CHUNK_OVERLAP}-word overlap, max "
                         f"{config.MAX_CHUNKS_PER_FILING} chunks per filing",
           "One fact-dense paragraph per chunk. Overlap keeps a number with the sentence that explains it. "
           "Small chunks rank more precisely than whole documents."],
          ["Contextual header", "Every chunk starts with: company (ticker) | date | category + headline",
           "A chunk saying \"revenue up 18%\" has no company name on its own. The header lets both vector and "
           "keyword search connect it to the right company and date."],
          ["Embeddings", f"{config.EMBED_MODEL} (384-d) via fastembed / ONNX, query prefix for bge",
           "Top-tier small retrieval model; runs on CPU without PyTorch, so the app fits a free 512 MB server."],
          ["Vector store", "FAISS IndexFlatIP on normalised vectors (= cosine), metadata filter via IDSelector",
           "Exact search is instant at this size; filtering inside FAISS means \"only Ashok Leyland\" is enforced, "
           "not hoped for."],
          ["Keyword index", "BM25 (Okapi, k1=1.5, b=0.75) written by us on numpy postings, built at ingest and saved", "Exact tickers, names, numbers and jargon (QIP, NCLT). Our version gives the same scores as the rank_bm25 library but uses ~10 MB instead of ~120 MB."],
      ], [26 * mm, 62 * mm, W - 88 * mm])]

s += [Paragraph("5. The big idea: understand the question before searching", H2),
      Paragraph("Basic RAG embeds the question and takes the 8 nearest chunks. That fails in predictable ways on "
                "this data, so each failure got a targeted fix:", P),
      table([
          ["Basic RAG fails because...", "TideBot fix"],
          ["\"Tata Power\" and \"Tata Steel\" have almost identical embeddings",
           "Company detection (full name, unique prefix, ticker in capitals, typo-tolerant fuzzy match) becomes a "
           "hard FAISS filter. The company filter is never relaxed: wrong company is worse than \"not found\"."],
          ["\"yesterday\", \"on Friday\", \"last 3 days\" mean nothing to an embedding",
           "Date parser turns them into a date range, anchored to the <b>latest date in the data</b> (so the demo "
           "still works next week)."],
          ["\"Which companies declared a dividend?\" needs ALL of them, top-8 returns 8",
           "List route: metadata query over every matching filing, sorted by importance, total count reported."],
          ["\"Compare A and B\" lets A's chunks crowd out B",
           "Query decomposition: one sub-question and one retrieval per company/aspect, then one combined answer."],
          ["Unknown names (\"Tesla\") still return the 'closest' filing",
           "Unknown-entity check against the corpus vocabulary, plus a calibrated similarity threshold "
           f"({config.MIN_DENSE_SCORE}) for off-topic questions."],
          ["Advice and price questions get a confident made-up answer",
           "Advice route refuses and shows facts instead; live-price route explains we hold filings, not prices."],
      ], [62 * mm, W - 62 * mm])]

s += [Paragraph("6. Retrieval pipeline (lookup route)", H2)]
s += bl(["<b>Filter</b> by company / date / category (hard constraints).",
         f"<b>Dense:</b> FAISS top {config.DENSE_CANDIDATES}.  <b>Sparse:</b> BM25 top {config.BM25_CANDIDATES}.",
         f"<b>Reciprocal Rank Fusion</b> (k={config.RRF_K}): score = &Sigma; 1/(k + rank). Uses ranks, so cosine (0-1) "
         "and BM25 (0-30) never need to be on the same scale.",
         f"<b>Diversity:</b> max {config.MAX_CHUNKS_PER_DOC} chunks per filing, so one long PDF can't take all slots.",
         f"<b>Cross-encoder rerank</b> ({config.RERANK_MODEL}) of the top {config.RERANK_POOL}: reads question and chunk "
         f"together; keep top {config.TOP_K}. On by default locally, <b>off on the free server</b>: it costs extra memory, and "
         "the evaluation passed every question with or without it (it changed the top-3 for only 3 questions).",
         "<b>Relaxation:</b> if a category or date filter returns nothing, drop it, say so in the trace, and retry."])

s += [Paragraph("7. Generation and grounding", H2)]
s += bl(["<b>Prompt rules:</b> use only numbered SOURCES; cite every fact as [n]; copy figures exactly; reply "
         "NOT_FOUND if unsupported; answer the part you can if partly supported; never give advice. Temperature 0.1.",
         "<b>Citation cleanup:</b> any [n] that doesn't exist is removed.",
         "<b>Number verification (faithfulness check):</b> every number in the answer is searched for in the sources; "
         "the UI shows \"5/5 numbers verified\" or lists the ones it could not find.",
         "<b>Resilience:</b> Groq llama-3.3-70b -> gpt-oss-120b -> llama-3.1-8b -> Gemini -> extractive answer from the "
         "filings. The demo never shows an error screen.",
         "<b>Follow-ups:</b> \"what about their dividend?\" reuses the last company discussed."])

s += [Paragraph("8. Streamlit UI", H2)]
s += bl(["Chat with history, example-question buttons, answer badges (sources, numbers verified, not-in-data / no-advice).",
         "<b>Sources</b> panel: company, date, category, excerpt, vector / BM25 / rerank scores, link to the original PDF.",
         "<b>How I found this</b> panel: route, detected companies, date and category filters, sub-questions, model, latency.",
         "Sidebar toggles for <b>hybrid</b>, <b>reranking</b> and <b>decomposition</b>: switch one off live in the demo "
         "to show why it matters."])

rows = [["#", "Type", "Question", "A", "B", "C"]]
for i, r in enumerate(ev["rows"], 1):
    rows.append([i, r["type"], r["q"], "pass" if r["A"] else "fail", "pass" if r["B"] else "fail",
                 "pass" if r["C"] else "fail"])
s += [Paragraph("9. Evaluation", H2),
      Paragraph(f"{N} questions covering factual lookups, tickers, typos, lists, dates, comparisons, multi-part, advice, "
                "live prices, out-of-window, off-topic and companies that aren't in the data. A pass needs the right "
                "filings retrieved (company / category / date) <i>and</i> the right behaviour (answer vs. refuse). "
                "<b>A</b> = plain vector RAG, <b>B</b> = hybrid search only, <b>C</b> = full TideBot. Run in the deployed configuration "
                "(reranker off).", P),
      table([["System", "Passed"], ["A. Baseline vector RAG", pct(S["baseline_vector_only"])],
             ["B. + Hybrid BM25 + RRF (no query understanding)", pct(S["hybrid_rerank"])],
             ["C. TideBot (query understanding + routing + fallbacks)", pct(S["tidebot_full"])],
             ["Numbers in answers found in sources", S["numbers_verified"]],
             ["Average response time (full system)", f"{S['avg_latency_s']} s"]], [110 * mm, W - 110 * mm]),
      Spacer(1, 5),
      table(rows, [8 * mm, 30 * mm, W - 80 * mm, 14 * mm, 14 * mm, 14 * mm])]

s += [Paragraph("10. Failure cases and how we'd fix them", H2)]
s += bl(["<b>Scanned PDFs have no text</b> (photos of signed letters): those filings only have a headline, so detailed "
         "questions get thin answers. <i>Fix:</i> OCR, or a vision model as Market Tide does in production.",
         "<b>Financial result tables</b> extract as jumbled numbers, so \"what was the profit?\" can miss. "
         "<i>Fix:</i> table-aware parsing, or store the AI summary with key figures as its own chunk.",
         "<b>Generic headlines</b> (\"informed the Exchange about Credit Rating\") hide the direction (upgrade or "
         "downgrade) unless the PDF text was readable. <i>Fix:</i> extract structured fields (rating agency, old/new rating).",
         "<b>Category labels come from rules</b>, so a few filings are mis-tagged and a strict category filter can miss "
         "them. <i>Mitigation:</i> relaxation step; <i>fix:</i> LLM tagging at ingest time.",
         "<b>Similarity threshold is narrow</b> (on-topic 0.675 and up, off-topic up to 0.632 on our probe set). <i>Mitigation:</i> second "
         "layer is the LLM's NOT_FOUND rule plus the unknown-name check."])

s += [Paragraph("11. Run it, deploy it, demo it", H2),
      code("python -m venv .venv && .venv\\Scripts\\activate\npip install -r requirements.txt\n"
           "copy .env.example .env      # add GROQ_API_KEY\n"
           "streamlit run chatbot/app.py\n"
           "python eval/run_eval.py     # re-run the evaluation"),
      Paragraph("<b>Deploy:</b> Render web service, start command "
                "<font name='Mono'>streamlit run chatbot/app.py --server.port $PORT --server.address 0.0.0.0</font>, "
                "secret <font name='Mono'>GROQ_API_KEY</font> set in Render's Environment tab. The index is committed, so "
                "the server never re-embeds. Memory: ~360 MB steady (limit 512 MB) after replacing rank_bm25 and turning the "
                "reranker off (TIDEBOT_RERANK=0). Free tier sleeps after 15 min: open it 2 minutes before presenting.", P),
      Paragraph("5-minute demo script", H3)]
s += bl(["<b>0:00 Problem (45 s):</b> thousands of filings a week; ChatGPT can't know this week's filings; we built "
         "TideBot on real NSE data.",
         "<b>0:45 Factual:</b> \"How much dividend did Ashok Leyland declare?\" -> show citation + Sources + PDF link.",
         "<b>1:30 List:</b> \"Which companies declared a dividend this week?\" -> all of them, with the total count.",
         "<b>2:10 Compare:</b> two companies -> open \"How I found this\" to show the sub-questions.",
         "<b>2:50 Honesty:</b> \"Should I buy Reliance?\" and \"What did Tesla announce?\" -> refusal / not in data.",
         "<b>3:30 Why hybrid:</b> toggle hybrid off and ask a ticker question, then show the ablation numbers.",
         "<b>4:00 Q&amp;A.</b> Likely questions: why 180-word chunks? (Section 4) Why FAISS? (exact + fast + filters) "
         "How do you stop hallucination? (Section 7) What fails? (Section 10)"])

doc = SimpleDocTemplate(str(ROOT / "docs" / "3_TideBot_How_We_Built_It.pdf"), pagesize=A4, leftMargin=18 * mm,
                        rightMargin=18 * mm, topMargin=15 * mm, bottomMargin=16 * mm,
                        title="TideBot: How We Built It and Why", author="Market Tide team")


def footer(c, d):
    c.saveState()
    c.setFont("Body", 7.5)
    c.setFillColor(GREY)
    c.drawString(18 * mm, 10 * mm, "TideBot: How We Built It and Why")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {d.page}")
    c.restoreState()


doc.build(s, onFirstPage=footer, onLaterPages=footer)
print("written docs/3_TideBot_How_We_Built_It.pdf")
