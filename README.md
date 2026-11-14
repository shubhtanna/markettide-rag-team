# Market Tide: RAG Chatbot (class assignment)

A RAG chatbot that answers questions about the **last 7 days of NSE corporate filings**.
This repo is separate from the live Market Tide product. It has no keys, no database and
no connection to the real website.

## What's here

| Folder | What it is |
|---|---|
| `site/` | Read-only copy of the Market Tide home page. Nothing is clickable except **Ask the Chatbot**. Plain HTML/CSS, no backend. |
| `data/filings_last_7_days.csv` | 2,766 important filings, 9 to 15 Nov 2026, from public NSE disclosures. |
| `docs/` | Project overview and RAG plan PDFs. **Read these first.** |
| `chatbot/` | The Streamlit chatbot we will build. |
| `tools/build_home.py` | Rebuilds `site/index.html` from the CSV. |

## Run the home page locally

```bash
python -m http.server 8000 --directory site
```

Then open http://localhost:8000.

## The dataset

One row per filing: `id, date, time, exchange, company, ticker, category, tag,
importance_score, headline, summary, description, pdf_url, page_url`.

- Source: public NSE corporate announcements (equities, SME, debt, InvITs/REITs),
  filtered to remove routine paperwork (importance score >= 45), with duplicates merged.
- BSE is **not included**: BSE's site refused automated requests during the export.
- `summary` is **empty for now**. `description` is built from company + category + date + headline.
  Headlines are short, so we will add AI summaries before building the chatbot.

## Secrets

The home page needs **no keys**. The chatbot needs **one free LLM key per person** (Groq or
Gemini). Copy `.env.example` to `.env` and fill it in. `.env` is gitignored, so never commit it.

*For information only. Not investment advice.*
