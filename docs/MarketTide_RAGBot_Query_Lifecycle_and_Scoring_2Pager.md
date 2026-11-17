# MarketTide RAGBot: Backend Query Lifecycle, Retrieval & Scoring Architecture
**A Deep-Dive Technical Guide to Query Processing, Vector Storage, Chunking, RRF & Scoring**  
*Technical Architecture Document · Engineering Team: Shreyansh Shailesh, Shubh Tanna, David Jeremie Anand, Shaurya Gupta*

---

# [PAGE 1] Query Lifecycle, Vector Database & Chunking Strategy

### 1. What Happens in the Backend When a User Enters a Query

When a user types a query or company name into the search box and presses Enter, the backend executes an automated 7-stage assembly pipeline:

```
[User Query Input]
       │
       ▼
[Stage 1: Sanitization & Defensive Guardrail Gate] ──▶ Slang / Non-corporate blocked in 0 ms
       │ (Valid query passes)
       ▼
[Stage 2: Entity Extraction & Conglomerate Router] ──▶ Resolves "Tata" to TMPV, TATAPOWER, TATASTEEL, TCS
       │
       ▼
[Stage 3: Parallel Dual Search Execution]
       ├─▶ Dense Vector Search: np.dot(embeddings, query_vec) on 384-dim normalized array
       └─▶ Sparse Lexical Search: BM25Okapi token frequency scoring
       │
       ▼
[Stage 4: Reciprocal Rank Fusion (RRF)] ──▶ Merges rank positions: Score = Σ w / (60 + rank)
       │
       ▼
[Stage 5: Query Relevance Scoring & Filtering] ──▶ Exact ticker (+80), Company (+40), Threshold (>= 35)
       │
       ▼
[Stage 6: Grounded LLM Context Assembly] ──▶ Packages Top-5 verified disclosures into prompt
       │
       ▼
[Stage 7: Groq Cloud LPU Inference & UI Render] ──▶ Llama-3.3 70B streams answer in < 650 ms + PDF cards
```

1. **Stage 1 — Defensive Guardrail Gate ($0\text{ ms}$)**:
   - Intercepts conversational greetings, slang, or insults (*"are you dumb?"*) at zero latency before invoking search.
   - Enforces whole-word regex boundaries (`\b`) to stop substring false positives (e.g. preventing `"am"` in *"am i god?"* from matching *Dhampur Bio Organics*).
   - Intercepts foreign tickers (Apple, Google, Tesla) and clarifies they trade on NASDAQ/NYSE, not NSE.
2. **Stage 2 — Conglomerate Multi-Hop Expansion**:
   - If a conglomerate family name is detected (e.g., *"Tata"*), the router dynamically resolves it into all operating subsidiaries: **TMPV** (Motors), **TATAPOWER**, **TATASTEEL**, and **TCS**, gathering filings across all subsidiaries simultaneously.
3. **Stage 3 — Parallel Dual Retrieval**:
   - Runs dense semantic vector search and sparse BM25 keyword search concurrently across 2,766 filings.
4. **Stage 4 & 5 — RRF Fusion & Relevance Scoring**:
   - Combines dense and sparse rankings using Reciprocal Rank Fusion and applies query match weights.
5. **Stage 6 & 7 — LLM Generation & Result Delivery**:
   - Packages the top-5 verified chunks into a strict context prompt. **Llama-3.3 70B** on **Groq Cloud LPUs** streams the executive synthesis in $< 650\text{ ms}$, rendering result cards with official signed NSE PDF links.

---

### 2. The Vector Database: Why an In-Memory Memory-Mapped Vector Store?

*Professor/Evaluator Question: "What vector database are you using?"*

We use an **in-memory, memory-mapped NumPy vector store (`embeddings.npy`) with exact cosine dot-product matrix multiplication**, rather than an external cloud vector database (like Pinecone, Weaviate, or Qdrant).

#### Why This Technical Decision Was Made:
1. **Dataset Nature**: The regulatory corpus consists of 2,766 verified filings from an active 7-day reporting cycle. The entire embedding matrix for 2,766 filings with 384-dimensional vectors requires just **$4.24\text{ MB}$** of RAM.
2. **Zero Network Latency**: Cloud vector databases introduce 50–150 ms of network round-trip HTTP overhead per query. Our in-memory matrix multiplication executes in **$68\text{ milliseconds}$** locally:
   $$\text{Sims} = \mathbf{E}_{\text{sub}} \cdot \mathbf{q}_{\text{normalized}}$$
3. **Zero Maintenance & Cost**: Eliminates API keys, monthly cloud hosting bills, and cold-start connection timeouts.
4. **Deterministic Reproducibility**: Binary cache files (`embeddings.npy`, `bm25.pkl`, `metadata.pkl`) package cleanly inside the Git repository ($9.07\text{ MB}$ total), enabling instant startup on any machine in $< 2\text{ seconds}$.

---

### 3. Chunking Strategy: Semantic Schema-Aware Structured Chunking

*Professor/Evaluator Question: "What type of chunking did you use?"*

Instead of naive fixed-character chunking (e.g., splitting every 500 characters with 50-character overlap), we implemented **Semantic Schema-Aware Structured Chunking (Document-Level Regulatory Chunking)**.

#### Why Fixed-Token Chunking Fails in Finance:
If you blindly split text at character 500, a sentence like *"Consolidated Net Profit rose 24.5% to ₹1,420 Crores"* gets cut in half (*"Consolidated Net Profit rose 24."* in chunk 1, *"5% to ₹1,420 Crores"* in chunk 2). The model loses the company name, date, or financial context, creating hallucinations.

#### Our Semantic Chunking Pipeline (`chatbot/ingest.py`):
Every regulatory filing is preserved as an **atomic, self-contained semantic document**, combining metadata and textual content into an enriched search string:
$$\text{Chunk} = \text{Date: } \{d\} \parallel \text{Time: } \{t\} \parallel \text{Exchange: NSE} \parallel \text{Company: } \{c\} \parallel \text{Ticker: } \{k\} \parallel \text{Category: } \{cat\} \parallel \text{Headline: } \{h\} \parallel \text{Details: } \{desc\}$$
- **Entity Preservation**: The company name, stock ticker, filing date, and exchange are permanently embedded in every chunk, guaranteeing that every retrieved passage has complete factual grounding.

---

\newpage

# [PAGE 2] Reciprocal Rank Fusion, Scoring Logic & UI Cards

### 4. Reciprocal Rank Fusion (RRF): How We Merge Search Rankings

Dense vector search and sparse BM25 search produce completely different score scales:
- Dense Vector Similarity produces Cosine Dot-Products bounded between $[-1.0, 1.0]$.
- BM25 Okapi produces unbounded positive term-frequency scores $[0, \infty)$.

Normalizing and blending these raw scores directly introduces severe mathematical calibration errors. Instead, we use **Reciprocal Rank Fusion (RRF)**—an algorithm from information retrieval that merges documents based on their **rank position** rather than raw scores:

$$\text{RRF Score}(d) = \sum_{m \in \{\text{dense}, \text{sparse}\}} \frac{w_m}{k + \text{rank}_m(d)}$$

- **The Smoothing Constant ($k = 60$)**: A standard parameter that prevents a document ranked #1 on a single list from unfairly dominating a document that ranked #2 on both lists.
- **The Result**: Filings that are strong in **both** semantic meaning (Vector) and exact ticker spelling (BM25) achieve the highest combined RRF score and are selected as the **Top-5 verified candidates**.

---

### 5. Scoring Breakdown: Query Relevance Score vs. Card Importance Score

There are **two distinct scores** in the system. Understanding the difference is critical:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           THE TWO SCORING SYSTEMS                               │
├───────────────────────────────────────┬─────────────────────────────────────────┤
│ 1. QUERY RELEVANCE SCORE (Internal)   │ 2. CARD IMPORTANCE SCORE (Visible)      │
│ • Determines the ranking order        │ • Displayed on the card (e.g. "Score: 68")│
│ • Calculated per user search          │ • Permanent attribute of the filing     │
│ • Exact Ticker match:       +80 pts   │ • Board Meeting / Q2 Results:  65-80 pts│
│ • Company Name match:       +40 pts   │ • Concalls / Capacity / JV:    55-64 pts│
│ • Headline match:           +25 pts   │ • Volume Spurt intimations:    45-54 pts│
│ • Narrative Body match:     +12 pts   │ • Routine admin paperwork:     < 45 pts │
│ • Importance Boost:   Score * 0.15    │   (Systematically excluded from DB)     │
└───────────────────────────────────────┴─────────────────────────────────────────┘
```

#### A. The Internal Query Relevance Matching Score (`site/filings_data.js` & `retriever.py`):
When a user searches a company name or ticker (e.g. `"Tata Power"` or `"TATAPOWER"`):
1. **Ticker Exact Match**: If the query matches the filing ticker (`TATAPOWER`), the filing receives an immediate **$+80$ point boost**.
2. **Company Name Match**: If the query tokens match the corporate name, it receives **$+40$ points**.
3. **Headline & Description Match**: Matching headline tokens adds **$+25$ points**; description body adds **$+12$ points**.
4. **Importance Multiplier**: To ensure high-impact news appears before minor notices, a bonus is added:  
   $$\text{Final Ranking Score} = \text{Match Points} + (\text{importance\_score} \times 0.15)$$
5. **Relevance Barrier ($\ge 35$)**: Only filings scoring 35 or higher are returned. If zero filings cross this barrier, the query is rejected as having no relevant disclosures.

#### B. The Visible Card Importance Score (e.g. `Score: 68`, `Score: 64`):
The score displayed on each result card is the filing's **Institutional Regulatory Importance Rating (0–100 scale)**:
- **Financial Materiality (Score 65–80+)**: Formal Board Meeting Financial Outcomes (`Outcome of Board Meeting`, Audited/Unaudited Q2 results), Press Releases with full earnings, Scheme of Arrangements, Demergers, Share Buybacks, and Rights Issues.
- **Corporate Developments (Score 55–64)**: Analysts/Investor Concall transcripts, Capital Additions, Executive KMP Appointments/Resignations, and JV Agreements.
- **Market Monitoring (Score 45–54)**: Official Exchange clarification letters on unusual volume surges ("Spurt in Volume").
- **Routine Filings (Score $< 45$)**: Administrative compliance certificates under Reg 74(5) or newspaper clippings (these are filtered out before indexing so users never see low-value clutter).

---

### 6. How the Results Are Shown on the Screen

When the backend finishes processing, the interface renders three coordinated visual panels:
1. **Executive Synthesis Card**: Generated by Groq Llama-3.3 70B in $< 650\text{ ms}$, summarizing the key corporate developments, involved subsidiaries, and average importance score.
2. **Verified Filing Dossiers**: Interactive cards displaying stock ticker badges, company names, timestamps, category tags, importance scores, and direct clickable links to the **official signed NSE PDF filings**.
3. **Execution Latency Timeline**: Millisecond telemetry showing the exact time taken by each component (*Gate: 0ms $\to$ Hybrid Search: 68ms $\to$ Groq LLM: 510ms*).
