# 🌊 MarketTide — Autonomous RAG Regulatory Chatbot

An autonomous multi-hop Retrieval-Augmented Generation (RAG) intelligence assistant for **2,766 statutory National Stock Exchange (NSE) corporate disclosures** (reporting window: November 9–15, 2026).

This branch (`RAG-Chatbot`) is **entirely independent** and configured to **directly launch and land on the RAG Chatbot interface**.

---

## ⚡ Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Configure Environment Key
Copy `.env.example` to `.env` and insert your free Groq API key:
```bash
cp .env.example .env
```
In `.env`:
```bash
GROQ_API_KEY=gsk_your_key_here
```
*(Get a free key in 30 seconds at [https://console.groq.com/keys](https://console.groq.com/keys))*

### 3. Launch the Chatbot
Run any of the following — they all land directly on the chatbot interface:

```bash
# Option A: Standard Streamlit Runner (Recommended)
streamlit run app.py

# Option B: Direct Python Execution
python app.py

# Option C: Shell Runner
./run.sh
```

Terminal will launch directly at: **`http://localhost:8501`**

---

## 🏗️ Architecture & Features

- **Hybrid Dense + Sparse Search**: Dense semantic vector embeddings (`all-MiniLM-L6-v2`) + BM25 Okapi with Reciprocal Rank Fusion (RRF).
- **Strict Zero-Hallucination Guardrails**:
  - Direct out-of-domain and conversational rejection (*"I don't have filings for that query"*).
  - Cross-validation against indexed corporate entities.
  - Zero false-positive source citations.
- **Multi-Hop Conglomerate Routing**: Automated entity resolution for groups like Tata Group (25 filings across TMPV, TATAPOWER, TATASTEEL, TCS), Adani, and Reliance.
- **Verifiable Audit Dossiers**: Every cited statement includes timestamp, category tag, importance score, and official NSE PDF links.
- **Process Execution Timeline**: Inspect retrieval stages, execution latencies (ms), and similarity match rankings.

---

## 🌐 Web & Cloud Deployment
- **Streamlit Community Cloud**: Ready out-of-the-box (`app.py` & `streamlit_app.py`).
- **Render**: Blueprint configured via `render.yaml`.
- **Docker / Heroku**: Configured via `Procfile`.
