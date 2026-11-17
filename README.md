# Market Tide: Spatial Financial Intelligence chatbot (Streamlit)

A RAG chatbot over **2,766 NSE corporate filings (9–15 Nov 2026)**. This branch holds **only the chatbot**.

## Run it

```bash
python -m venv .venv
.venv\Scripts\activate            # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env            # then paste your GROQ_API_KEY into .env
streamlit run chatbot/app.py
```

Open http://localhost:8501.

## How it works

- **UI:** `chatbot/spatial_ui/index.html` is the Spatial Financial Intelligence page, served as a Streamlit
  custom component and shown full-screen. When you search, the page sends the question to Streamlit's Python
  backend and shows the answer it returns. Opened on its own (outside Streamlit), the page falls back to its
  original in-browser keyword search.
- **Backend (`chatbot/agent.py`, `tools.py`, `retriever.py`):** guard rails (advice, out-of-domain, non-NSE,
  out-of-window), company and conglomerate routing, and hybrid retrieval (BM25 + MiniLM vectors, RRF).
  The pre-built index is in `chatbot/cache/`.
- **Answering (`chatbot/grounding.py`, adapted from MedEvolv Mentor):**
  - The evidence is numbered `[1]..[n]`: each filing's headline plus the matching part of its PDF text
    (`data/filings_enriched.csv`).
  - The model writes a draft at temperature 0 and must cite every claim.
  - A deterministic fact check runs before anything is shown: every citation must be real, and every number
    and company named must appear in the passage it cites.
  - One rewrite is allowed; if it still fails, the failing sentences are dropped. If nothing verified is
    left, the bot replies "I don't know".
  - `[n]` in the answer is row n of the filings table.

## Evaluate

```bash
python eval/product_eval.py       # 26 questions incl. traps -> eval/product_eval.md
python -m pytest tests -q         # guard-rail tests
```

Groq's free tier allows about 200k tokens per day on `gpt-oss-120b` (roughly 60–70 questions). Running the full
evaluation uses a large part of that.

*For information only. Not investment advice.*
