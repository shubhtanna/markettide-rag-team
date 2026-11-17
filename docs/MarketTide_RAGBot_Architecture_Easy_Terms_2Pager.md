# MarketTide RAGBot: Architecture & Technical Workflow
**An Accessible, Plain-Terms Guide to How the Query Pipeline, Matching, and UI Work**  
*Academic Project Specification · Engineering Team: Shreyansh Shailesh, Shubh Tanna, David Jeremie Anand, Shaurya Gupta*

---

# [PAGE 1] System Overview, Data Foundation & Query Pipeline

### 1. High-Level Overview: What MarketTide RAGBot Does

#### The Problem:
If you ask a general AI model like ChatGPT: *"What did Tata Motors announce about their Q2 financials?"*, it often guesses or hallucinates numbers based on old web data. In corporate finance and regulatory compliance, making an investment decision on a hallucinated number or fake board meeting outcome is dangerous.

#### Our Solution:
**MarketTide RAGBot** is a domain-specific, **zero-hallucination regulatory search engine** for the Indian stock market.
- **100% Grounded in Exchange Filings**: It answers questions strictly using verified corporate announcements submitted to the **National Stock Exchange of India (NSE)**.
- **Verifiable PDF Proof**: Every answer includes clickable links to the **official signed PDF documents** submitted by company secretaries.
- **Refusal to Hallucinate**: If you ask an irrelevant question (*"are you dumb?"*, *"tell me a joke"*), or ask about a company with no filings, the system refuses to answer rather than making up false stories.
- **Two Delivery Modes**:
  1. **Interactive Chatbot Terminal** (`RAG-Chatbot` branch): Built on Streamlit, showing live step-by-step pipeline execution times and filing cards.
  2. **Spatial 3D Workstation** (`shrey` branch): Built on Three.js, featuring 3D stock trajectory lines and an executive search dock.

---

### 2. The Data Foundation: What Lives in the Engine

We do not use unverified news or social media rumors. The engine is powered exclusively by official statutory filings:

| Data Parameter | Exact System Details |
|---|---|
| **Primary Data Source** | Official corporate regulatory announcements from the **National Stock Exchange of India (NSE)**. |
| **Time Period** | Active 7-day reporting cycle: **November 9 to November 15, 2026** (an active quarterly earnings week). |
| **Scale & Scope** | **2,766 verified corporate filings** across **1,716 publicly listed Indian companies**. |
| **Legal Mandate** | Compliance under **SEBI (LODR) Regulations 2015**: Regulation 30 (Material Events), Regulation 33 (Financial Results), and Regulation 42 (Corporate Actions). |
| **Event Categories** | Quarterly Financial Results (Audited & Unaudited), Board Meeting Outcomes, Share Buybacks, Rights Issues, Spurt in Trading Volume notices, Demergers, and Executive Changes. |
| **Importance Threshold** | Filings are rated from 0 to 100 on regulatory impact. Low-value administrative paperwork is eliminated, retaining filings with **score $\ge 45$**. |
| **Pre-Computed Cache** | All filings, vectors, and word matrices are saved in a **$9.07\text{ MB}$ local cache** (`embeddings.npy` 4.2MB, `bm25.pkl` 1.2MB, `metadata.pkl` 3.6MB) for instant boot under 2 seconds. |

---

### 3. The Query Journey: What Happens When You Type in the Box

When a user types a query into the search box and presses Enter, it moves through a 5-station pipeline:

```
[User Types Query]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ Station 1: The Pre-Check Filter (Defensive Guardrails)  │
│ • Slang / Insult Check: Blocks queries like "are you dumb?" in 0 ms
│ • Whole-Word Regex (\b): Prevents "am" in "am i god?" from matching Dhampur
│ • Foreign Ticker Check: Clarifies Apple/Tesla trade on NASDAQ, not NSE
└──────────────────────────┬─────────────────────────────┘
                           │ Valid Corporate Query
                           ▼
┌────────────────────────────────────────────────────────┐
│ Station 2: The Multi-Hop Conglomerate Router           │
│ • "Tata Group" automatically expands into:             │
│   Tata Motors (TMPV), Tata Power, Tata Steel, and TCS  │
└──────────────────────────┬─────────────────────────────┘
                           │ Expanded Targets
                           ▼
┌────────────────────────────────────────────────────────┐
│ Station 3: Hybrid Search (Vectors + BM25)              │
│ • Vector Search: Understands meaning & synonyms        │
│ • BM25 Search: Finds exact tickers and legal numbers   │
└──────────────────────────┬─────────────────────────────┘
                           │ Top 20 Candidates from Each
                           ▼
┌────────────────────────────────────────────────────────┐
│ Station 4: The Matchmaker (Reciprocal Rank Fusion - RRF│
│ • Merges both scoreboards mathematically to pick Top 5 │
└──────────────────────────┬─────────────────────────────┘
                           │ Top 5 Verified Chunks
                           ▼
┌────────────────────────────────────────────────────────┐
│ Station 5: LLM Synthesis & UI Display                  │
│ • Groq Llama-3.3 70B streams answer in < 650 ms        │
│ • Screen displays Summary + Dossiers + Signed PDF links│
└────────────────────────────────────────────────────────┘
```

---

\newpage

# [PAGE 2] Matching Logic, Result Presentation & Applications

### 4. How We Match: The Dual Search Engines & Rank Fusion

How does the engine find the exact right filing out of 2,766 documents in just **68 milliseconds**? It uses two search engines running in parallel:

1. **Search Engine 1: Semantic Vector Search (`all-MiniLM-L6-v2`)**:
   - Converts the query into a 384-dimensional mathematical coordinate.
   - **What it does best**: Matches *meaning and intent*. If a user asks *"returning money to shareholders"*, it knows that means *"share buyback"* or *"dividend"*, even though the words are completely different.
2. **Search Engine 2: Exact Keyword Search (BM25 Okapi)**:
   - A term-frequency statistical search algorithm.
   - **What it does best**: Matches *exact legal symbols and numbers*. It finds exact stock codes like `TMPV`, `TATAPOWER`, or regulatory clauses like `Regulation 30`.
3. **The Matchmaker: Reciprocal Rank Fusion (RRF)**:
   - Both engines return their Top 20 best candidate filings.
   - The system combines their rankings using a balancing formula:
     $$\text{Combined Score}(d) = \frac{1}{60 + \text{Vector Rank}} + \frac{1}{60 + \text{BM25 Rank}}$$
   - Documents that rank high on **both** lists rise to the top. The system selects the **Top 5 cleanest filings**.

---

### 5. How We Show the Results: The 3-Part Output Display

When the search completes, the user interface displays three distinct sections:

1. **The Executive Synthesis Card**:
   - A concise, high-level summary written by **Llama-3.3 70B** running on **Groq Cloud LPUs** ($< 650\text{ ms}$ streaming latency).
   - Explains what was discovered, how many corporate entities were involved, and the overall average importance rating.
2. **The Verified Corporate Filing Dossiers**:
   - Individual cards for each supporting document showing:
     - **Ticker Badge**: Stock symbol (e.g. `TATAPOWER`, `TMPV`).
     - **Company Name**: Full legal entity name.
     - **Timestamp**: Exact filing date and time (e.g. `2026-11-11 17:39`).
     - **Category Tag**: Highlighted badge (e.g. `Results`, `Buyback`, `Spurt in Volume`).
     - **Importance Score**: Impact score (45 to 100).
     - **Official NSE PDF Link**: Clickable link opening the authentic signed exchange document.
3. **The Execution Step Timeline**:
   - Shows the exact stages the system took and the latency in milliseconds (e.g. *Query Routed: 2ms $\to$ Hybrid Retrieval: 68ms $\to$ Synthesis: 510ms*).

---

### 6. Real-World Applications & Use Cases

- **Application 1: Conglomerate Risk & Capital Tracking**:  
  Auditing a conglomerate like the **Tata Group** requires checking multiple distinct legal entities. MarketTide automatically searches across Tata Motors (TMPV), Tata Power, Tata Steel, and TCS simultaneously, giving analysts a single consolidated view across 25 filings.
- **Application 2: Corporate Action Due Diligence (M&A & Buybacks)**:  
  Investment bankers and compliance officers can instantly isolate high-impact statutory moves like share buybacks (e.g. Dhampur Bio Organics) or rights issues (e.g. DCM Shriram) without sorting through routine paperwork.
- **Application 3: Volume Spike ("Spurt in Volume") Clarification**:  
  When a stock moves unexpectedly, traders need to know if the company issued an official explanation. MarketTide surfaces official exchange volume clarification letters (e.g. TTML's trading volume response) to separate fact from speculation.
- **Application 4: Audit-Ready Financial Research**:  
  Every insight is tied to an authentic exchange filing, giving research analysts and compliance officers an audit trail that eliminates legal risk.

---

### 7. Software Technologies Used (The Complete Stack)

| Software Tool | Role in System | Why We Chose It |
|---|---|---|
| **Python 3.11 / 3.13** | Core Programming Language | Runs the data ingestion pipeline, mathematical ranking, and background API server. |
| **Streamlit** | Chatbot UI Framework | Provides the reactive terminal interface (`app.py`), execution timelines, and source dossiers. |
| **Three.js & WebGL** | 3D Graphics Library | Renders the interactive 3D stock trajectory lines and orbit camera controls on the landing page. |
| **Sentence-Transformers** | Embedding Model | Uses `all-MiniLM-L6-v2` for lightweight, fast 384-dimensional semantic matching on CPU. |
| **Rank-BM25** | Lexical Search Engine | Implements BM25Okapi to match exact company tickers and statutory clauses. |
| **Groq Cloud API** | LLM Inference Engine | Runs `llama-3.3-70b-versatile` on specialized LPU hardware for sub-second streaming answers. |
| **Pandas & NumPy** | In-Memory Data Processing | Performs fast tabular manipulation and matrix dot-product vector math in RAM. |
| **ReportLab** | PDF Generation Engine | Programmatically compiles formal 2-page publication PDFs with custom styling. |
