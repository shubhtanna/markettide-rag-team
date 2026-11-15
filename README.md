# TideBot: RAG chatbot over 7 days of NSE filings

A Retrieval-Augmented Generation chatbot that answers questions about Indian company filings
published on NSE in the last 7 days, and links every answer to the original filing PDF.
This repo is separate from the live Market Tide product. It has no keys, no database and no
connection to the real website.

**Read first:** [`docs/3_TideBot_How_We_Built_It.pdf`](docs/3_TideBot_How_We_Built_It.pdf) covers every
design decision, why it was made, and the evaluation results.

## What's here

| Path | What it is |
|---|---|
| `chatbot/app.py` | Streamlit chat UI |
| `chatbot/rag.py` | RAG engine: routing, decomposition, prompt, fallbacks, grounding check |
| `chatbot/retriever.py` | Metadata filter + FAISS vectors + BM25, fused with RRF, cross-encoder rerank |
| `chatbot/query_parser.py` | Detects companies, dates, categories and intent in a question |
| `chatbot/ingest.py` | Data -> chunks -> embeddings -> FAISS index (`chatbot/index/`, committed) |
| `chatbot/llm.py` | OpenAI / Groq / Gemini with automatic fallback |
| `eval/` | Test questions, ablation runner and results (`eval/results.md`) |
| `data/` | `filings_last_7_days.csv` (raw export) and `filings_enriched.csv` (+ PDF text) |
| `tools/` | PDF text enrichment, home page builder, explainer PDF builder |
| `site/` | Read-only copy of the Market Tide home page (static) |
| `docs/` | Project overview, RAG plan, and the "How we built it" explainer |

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # then put your OPENAI_API_KEY (or Groq / Gemini key) in .env
streamlit run chatbot/app.py
```

Without a key, the app still works but shows direct extracts from the filings instead of written answers.

## Rebuild / evaluate

```bash
python tools/enrich_pdf_text.py     # re-download PDF text (slow, resumable)
python chatbot/ingest.py            # rebuild the index
python eval/run_eval.py             # re-run the evaluation -> eval/results.md
python tools/build_explainer_pdf.py # refresh the explainer PDF with new numbers
```

## Data

Public NSE corporate announcements (equities, SME, debt, InvITs/REITs), filtered to drop routine
paperwork and de-duplicated. BSE is **not included** because BSE's site refused automated requests
during the export. The PDF text covers the first 6 pages of each filing; scanned PDFs have no text.

## Secrets

The home page needs **no keys**. The chatbot needs **one LLM key**: OpenAI, Groq or Gemini (set more than one and the next is a backup).
Locally it goes in `.env` (gitignored, never commit it); on Render it goes in the service's Environment tab.

## Team workflow

Work on a branch (`git checkout -b feature/your-change`), push it, and open a pull request into `main`.
Don't push straight to `main`.

*For information only. Not investment advice.*
