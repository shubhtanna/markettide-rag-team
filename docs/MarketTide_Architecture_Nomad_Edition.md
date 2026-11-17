# MarketTide RAGBot: The Plain-Language Architecture Guide
**An Intuitive, Non-Complex Explanation of How Our AI Financial Engine Works**  
*The Nomad Edition · Prepared by: Shreyansh Shailesh, Shubh Tanna, David Jeremie Anand, Shaurya Gupta*

---

# [PAGE 1] The Big Picture, The Data & The Two Scouts

### 1. The Core Idea: The Honest Scribe of the Great Bazaar

Imagine a massive marketplace—the **National Stock Exchange (NSE)**—where thousands of merchant families (companies) come to trade. Under royal rules (SEBI regulations), whenever a merchant has a major event—such as earning massive gold, buying back shares, or losing a chief elder—they must nail an official stamped letter to the public board.

Most travelers ask traveling storytellers (like standard ChatGPT) what happened in the market. But storytellers get tired, confuse merchant names, invent dates, and tell believable lies. In trading, trusting a false tale means losing your horses and gold.

**What We Made:**  
We built an **Honest Scribe System** called **MarketTide RAGBot**.
1. It does not tell fables or guess.
2. It answers questions **only** by pointing to real, stamped letters from the companies.
3. Every answer comes with the **original royal wax-sealed scroll (an official signed PDF)** so you can inspect the signature yourself.
4. If someone asks nonsense, or asks about a company with no letters, it frankly says: *"I have no scrolls on that topic."*

---

### 2. The Treasure Chest: What Data We Used

We did not gather rumors from roadside campfires. We collected **2,766 verified letters** from **1,716 merchant families** during one busy 7-day trading week (November 9–15, 2026):

- **The Types of Letters**:
  - *Treasury Reports (Q2 Earnings)*: How much gold the company made or lost.
  - *Clan Council Decisions (Board Outcomes)*: New projects, mergers, and director appointments.
  - *Gold Returns (Buybacks & Dividends)*: Returning capital to caravan owners.
  - *Sudden Dust Clouds (Spurt in Volume)*: Explaining why trading activity suddenly spiked.
- **The Filter**: Out of thousands of minor notices, we only kept high-impact letters (rated **45/100 or higher**).
- **The Pocket Pouch (9.07 MB)**: Instead of lugging heavy filing cabinets, we compressed all the letters, maps, and word indexes into a tiny digital pouch of just **9 megabytes** that opens in less than 2 seconds anywhere in the world.

---

### 3. Step 1 & 2 of the Architecture: The Gatekeeper and Clan Scouts

```
[Your Question] ──▶ [Gatekeeper at Tent Door] ──▶ [Clan Scout (Multi-Hop)]
                           │                               │
             Rejects nonsense in 0 ms         Expands "Tata Clan" into
             (e.g., "are you dumb?")          Power, Motors, Steel & Tech
```

#### Step 1: The Gatekeeper at the Tent Flap (Guardrails)
Before anyone enters our tent to search the scrolls, our Gatekeeper inspects the question:
- **Turning Away Clowns (0 ms)**: If a passerby shouts insults (*"are you dumb?"*) or asks philosophical riddles (*"am i god?"*), the Gatekeeper stops them at the entrance without waking up our master scribe.
- **Whole-Word Shield**: Naive scribes confuse small letters inside words. For example, if someone asks *"am i god?"*, a foolish scribe might see *"am"* and pull out scrolls from *Dh**am**pur Sugar*. Our Gatekeeper enforces whole-word boundaries so words never collide by accident.
- **Foreign Caravan Watch**: If someone asks about caravans from the distant Western Empire (*Apple, Google, Tesla*), the Gatekeeper politely reminds them: *"Those merchants trade across the ocean on the NASDAQ; they do not stamp scrolls at this Indian bazaar."*

#### Step 2: The Clan Scout (Multi-Hop Conglomerate Resolver)
In our market, great houses like the **Tata Clan** have many tents: *Tata Motors, Tata Power, Tata Steel, and TCS*. If you ask: *"What did the Tatas do this week?"*, our Clan Scout knows all 4 family tents. It gathers **25 separate scrolls** across the whole family at once.

---

\newpage

# [PAGE 2] The Search, The Council & The Master Scribe

### 4. Step 3 & 4: Two Different Scouts & The Balancing Scale

How do we find the exact right scroll out of 2,766 letters in just **68 milliseconds**? We send out **Two Different Scouts** at the same time:

```
                  ┌──▶ Scout 1: The Idea Scout (Dense Vector Embeddings)
                  │    "Finds scrolls that MEAN the same thing"
[Filtered Query] ─┤
                  └──▶ Scout 2: The Exact Word Tracker (BM25 Okapi)
                       "Finds scrolls with the EXACT ticker name"
                                  │
                                  ▼
                [The Council Table: Reciprocal Rank Fusion]
                "Balances both scout lists to find the Top 5"
```

1. **Scout 1 — The Idea Scout (Dense Vectors)**:
   - This scout doesn't care about exact words; it understands *intent*.
   - If you ask *"giving money back to shareholders"*, it knows that means *"share buyback"* or *"dividend"*, even if you didn't use those exact words.
2. **Scout 2 — The Exact Word Tracker (BM25)**:
   - This scout is a meticulous clerk. It looks for exact merchant codes like `TMPV`, `TATAPOWER`, or legal clauses like `SEBI Regulation 30`.
3. **The Council Table (Reciprocal Rank Fusion - RRF)**:
   - Both scouts run back with their top 20 candidate scrolls.
   - The Council places them on a mathematical balancing scale:
     $$\text{Combined Rank Score} = \frac{1}{60 + \text{Idea Rank}} + \frac{1}{60 + \text{Word Rank}}$$
   - The scrolls that both scouts agree on rise to the very top. We pick the **Top 5 cleanest scrolls**.

---

### 5. Step 5 & 6: The Master Scribe & The Two Viewing Tents

#### Step 5: The Master Scribe (Groq Cloud & Llama-3.3 70B)
Now, the 5 best scrolls are handed to our **Master Scribe**—a very fast, highly intelligent model (**Llama-3.3 70B** running on custom Groq silicon chips):
- **Ultra-Fast Speed**: It starts writing in less than half a second ($< 650\text{ ms}$).
- **Strict Honesty**: The scribe is under a sacred oath: it is forbidden from adding its own opinions or outside rumors. It summarizes *only* what is written on the 5 scrolls.
- **The Proof**: Under each summary sentence, it staples a badge showing the merchant code, date, importance score, and a direct link to the **original signed PDF filing**.

#### Step 6: The Two Viewing Tents (The Frontends)
We created two different ways for travelers to interact with our engine:

| Viewing Tent | Technology | What You Experience |
|---|---|---|
| **1. The Conversation Tent** (`RAG-Chatbot` branch) | **Streamlit** (Python) | A clean, focused terminal where you chat with the Scribe, inspect every step of its thinking, see search latencies in milliseconds, and view source document cards. |
| **2. The 3D Star Map** (`shrey` branch) | **Three.js & WebGL** | An executive trading desk featuring a living 3D constellation of stock lines that bend and curve in space, with a bottom search dock that springs open smoothly. |

---

### 6. The Nomad's Summary Table: Every Tool Explained Simply

| Tool Name | What a Tech Person Calls It | What It Actually Does in Plain Language |
|---|---|---|
| **Llama-3.3 70B** | Large Language Model (LLM) | The intelligent Master Scribe that reads the letters and writes clear human summaries. |
| **Groq Cloud** | LPU Hardware Accelerator | The supercharged engine that makes the Scribe write at lightning speed ($< 0.5\text{ s}$). |
| **Sentence-Transformers** | Dense Vector Embeddings | The "Idea Scout" that understands what your question actually means. |
| **Rank-BM25** | Lexical Search Engine | The "Word Scout" that checks for exact merchant tickers and legal codes. |
| **Streamlit** | Interactive UI Framework | The clean wooden desk where you sit down and chat with the Scribe. |
| **Three.js** | WebGL 3D Engine | The glowing 3D light-map showing stock prices floating in space. |
| **Pandas & NumPy** | Fast Memory Math | The ledger books that allow us to calculate scores in 68 milliseconds. |
| **NSE PDF Documents** | Ground Truth Regulatory Data | The real, wax-sealed letters that prove our answers are 100% true. |
