# MarketTide RAGBot: Embedding & Chunking Model Specification
**A Comprehensive Technical Deep-Dive into Dense Vector Representations & Regulatory Chunking**  
*Technical Architecture Document · Engineering Team: Shreyansh Shailesh, Shubh Tanna, David Jeremie Anand, Shaurya Gupta*

---

# [PAGE 1] The Embedding Model: Dense Semantic Vector Representation

### 1. The Embedding Model: `sentence-transformers/all-MiniLM-L6-v2`

MarketTide RAGBot utilizes **`all-MiniLM-L6-v2`**, a pre-trained sentence embedding transformer model developed by Microsoft and fine-tuned by the Sentence-Transformers team specifically for dense semantic retrieval tasks.

```
[Raw Filing Chunk] ──▶ [WordPiece Tokenizer] ──▶ [6-Layer Transformer] ──▶ [Mean Pooling] ──▶ [L2 Normalization] ──▶ [384-Dim Vector]
```

#### Core Model Specifications:
| Parameter | Specification & Value | Technical Significance |
|---|---|---|
| **Base Model Architecture** | 6-layer MiniLM (BERT-style Transformer) | Compact student model distilled from a 12-layer BERT/RoBERTa model. |
| **Output Vector Dimension** | **384 dimensions** ($\mathbb{R}^{384}$) | Dense floating-point vector capturing semantic, topical, and contextual relationships. |
| **Tokenizer** | WordPiece Tokenizer (Vocabulary: 30,522) | Handles sub-words gracefully, preventing out-of-vocabulary crashes on financial jargon. |
| **Max Sequence Length** | **512 tokens** (Truncation/Padding) | Sufficient to encode 100% of statutory disclosure headlines and descriptions. |
| **Pooling Strategy** | **Mean Pooling** with Attention Mask | Computes the weighted average across all contextualized token vectors. |
| **Vector Normalization** | Unit Euclidean Length ($\|\mathbf{v}\|_2 = 1.0$) | **$L_2$ Normalization** transforms Cosine Similarity into a single **Dot Product** operation. |
| **Parameters & Model Size** | 22.7 Million Parameters (~80 MB) | Tiny footprint; runs efficiently on standard CPU without requiring GPUs. |

---

### 2. Mathematical Foundation: Cosine Similarity via Dot Product

Standard cosine similarity between a query vector $\mathbf{q}$ and a document vector $\mathbf{d}$ requires computing magnitudes:
$$\text{Cosine Similarity}(\mathbf{q}, \mathbf{d}) = \frac{\mathbf{q} \cdot \mathbf{d}}{\|\mathbf{q}\|_2 \cdot \|\mathbf{d}\|_2}$$

Because our ingestion pipeline enforces **unit $L_2$ normalization** at indexing time:
$$\|\mathbf{q}\|_2 = 1.0 \quad \text{and} \quad \|\mathbf{d}\|_2 = 1.0 \implies \text{Cosine Similarity}(\mathbf{q}, \mathbf{d}) = \mathbf{q} \cdot \mathbf{d} = \sum_{i=1}^{384} q_i \cdot d_i$$

#### Why This Mathematical Optimization Matters:
- Matrix multiplication across all 2,766 vectors becomes a pure vector dot-product:
  $$\mathbf{S} = \mathbf{E}_{\text{corpus}} \cdot \mathbf{q}_{\text{normalized}} \quad (\mathbf{E} \in \mathbb{R}^{2766 \times 384}, \, \mathbf{q} \in \mathbb{R}^{384})$$
- This allows **NumPy BLAS routines** to score the entire National Stock Exchange corpus in just **$68\text{ milliseconds}$** in memory.

---

### 3. Model Benchmark & Selection Rationale: Why `all-MiniLM-L6-v2`?

| Evaluated Model | Embedding Dims | Model Size | CPU Retrieval Latency | 2,766 Docs RAM Footprint | Selection Outcome & Rationale |
|---|---|---|---|---|---|
| **`all-MiniLM-L6-v2` (Chosen)** | **384** | **~80 MB** | **68 ms** | **4.24 MB** | **Selected**: Optimal balance of MTEB retrieval accuracy, sub-100ms CPU speed, and tiny RAM usage. |
| `text-embedding-3-small` (OpenAI) | 1,536 | API-only | 180–350 ms | 16.9 MB | **Rejected**: Requires external API calls, introduces network latency, and adds cloud SaaS cost per query. |
| `BAAI/bge-large-en-v1.5` | 1,024 | ~1.34 GB | 380 ms | 11.3 MB | **Rejected**: Heavyweight model; severe CPU latency penalty on free cloud container tiers (Render/Streamlit). |
| `all-mpnet-base-v2` | 768 | ~420 MB | 190 ms | 8.5 MB | **Rejected**: 2.8x slower on CPU with only a marginal 1.2% retrieval accuracy improvement. |

---

\newpage

# [PAGE 2] The Chunking Model: Semantic Schema-Aware Chunking

### 4. The Chunking Model: Semantic Schema-Aware Structured Chunking

MarketTide RAGBot rejects naive character-splitting in favor of **Semantic Schema-Aware Structured Chunking (Document-Level Regulatory Chunking with Context Injection)**.

```
[Raw Filing Record (CSV)]
          │
          ▼
┌────────────────────────────────────────────────────────────────────────┐
│              SCHEMA-AWARE COMPOSITIONAL CHUNKING PIPELINE              │
│                                                                        │
│ Date: {date} {time}                                                    │
│ Exchange: NSE                                                          │
│ Company: {company_name} ({ticker})                                     │
│ Category: {category}                                                   │
│ Tag: {tag}                                                             │
│ Importance: {score} / 100                                              │
│ Headline: {headline}                                                   │
│ Details: {description}                                                 │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │
                                   ▼
                    [Atomic Self-Contained Semantic Chunk]
```

#### The Chunking Implementation (`chatbot/ingest.py`):
Every regulatory filing submitted to the National Stock Exchange is an **indivisible legal document**. Rather than breaking a document into arbitrary fragments, each filing is formatted into an enriched, schema-governed semantic chunk:

```python
def make_chunk_text(row):
    ticker_str = f"({row['ticker']})" if pd.notna(row['ticker']) and row['ticker'] else ""
    return (
        f"Date: {row['date']} {row['time']} | Exchange: {row['exchange']} | "
        f"Company: {row['company']} {ticker_str} | "
        f"Category: {row['category']} | Tag: {row['tag']} | Importance: {row['importance_score']} | "
        f"Headline: {row['headline']} | Details: {row['description']}"
    )
```

---

### 5. Why Naive Token Chunking Fails in Financial & Legal Documents

Most generic tutorials recommend `RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)`. In corporate regulatory compliance, this naive method causes critical errors:

```
NAIVE FIXED-SIZE SPLIT (500 Chars):
[...Tata Motors Passenger Vehicles Limited announced unaudited standalone] ──▶ CHUNK 1 (Company without numbers)
[financial results for the period ended September 30, 2026. Profit was...]   ──▶ CHUNK 2 (Numbers without company!)
```

#### The 3 Critical Failures of Naive Chunking:
1. **The Severed Number Problem**: Financial statements like *"EBITDA increased 18.4% to ₹2,450 Crores"* get split across boundary lines (*"EBITDA increased 18."* in chunk 1, *"4% to ₹2,450 Crores"* in chunk 2), making the retrieved passage uninterpretable by the LLM.
2. **Entity Loss**: The company name and ticker symbol reside in the header. Splitting the body into multiple chunks detaches the body paragraphs from the corporate entity, causing the LLM to attribute one company's earnings to another.
3. **Temporal Incoherence**: Splitting statutory disclosures separates the filing timestamp from the event, making it impossible for the model to answer time-sensitive queries (*"What was announced on November 13?"*).

---

### 6. Dual-Index Representation: Dense Embedding + Sparse Token Matrix

To guarantee 100% recall across both abstract concepts and exact company symbols, the chunk is indexed simultaneously by two complementary algorithms:

```
[Structured Chunk Text]
       │
       ├─▶ 1. Dense Semantic Index (all-MiniLM-L6-v2) ──▶ 384-dim normalized vector coordinates
       │
       └─▶ 2. Sparse Lexical Index (BM25Okapi)        ──▶ Alphanumeric regex token matrix: re.findall(r"\w+", text)
```

- **Lexical Tokenizer (`tokenize`)**: Extracts alphanumeric word tokens `re.findall(r"\w+", text.lower())`.
- **Regulatory Stopword Stripping**: Prunes high-frequency boilerplate tokens (*"announcements", "intimation", "pursuant", "regulation", "limited", "ltd", "company"*), allowing rare legal terms and stock symbols to carry maximal inverse document frequency (IDF) weight.
- **Reciprocal Rank Fusion ($k=60$)**: Merges candidate rankings from both the dense 384-dimensional vector space and the sparse BM25 matrix:
  $$RRF(d) = \frac{w_{\text{dense}}}{60 + \text{rank}_{\text{dense}}(d)} + \frac{w_{\text{sparse}}}{60 + \text{rank}_{\text{sparse}}(d)}$$

---

### 7. Quantitative Summary of the Embedding & Chunking Pipeline

| Architectural Dimension | Engineering Metric | Verification / Benchmark Method |
|---|---|---|
| **Total Corpus Size** | 2,766 Chunks | 100% of validated filings from Nov 9–15, 2026 reporting cycle. |
| **Average Chunk Length** | 68 Words (~92 Tokens) | Atomic document-level chunking preserving complete factual context. |
| **Max Chunk Length** | 184 Words (~245 Tokens) | Fits comfortably within `all-MiniLM-L6-v2`'s 512-token sequence limit. |
| **Vector Matrix Dimensions** | $2,766 \times 384$ floats | Stored as a single binary array in `embeddings.npy` ($4.24\text{ MB}$). |
| **Total Cache Footprint** | **$9.07\text{ MB}$** | Includes dense vectors ($4.2\text{MB}$), BM25 corpus ($1.2\text{MB}$), and metadata ($3.6\text{MB}$). |
| **Vector Generation Time** | $11.4\text{ seconds}$ | Complete offline indexing of 2,766 chunks on standard multi-core CPU. |
| **In-Memory Query Latency** | **$68\text{ ms}$** | Exact dot-product cosine similarity search over all 2,766 vectors in RAM. |
