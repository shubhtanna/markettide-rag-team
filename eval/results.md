# Evaluation results

- Questions: **32**  ·  LLM connected: **False**  ·  Reranker: **False**
- A. Baseline (vector only): **14/32**
- B. Hybrid search (no query understanding): **15/32**
- C. TideBot full system: **32/32**
- Numbers in answers found in sources: **n/a**
- Average latency (full system): **0.1s**

| # | Type | Question | A | B | C | Route | Status |
|---|---|---|---|---|---|---|---|
| 1 | factual | What did Ashok Leyland announce this week? | ✅ | ✅ | ✅ | lookup | answered |
| 2 | factual | How much interim dividend did Ashok Leyland declare? | ❌ | ❌ | ✅ | lookup | answered |
| 3 | factual | What did Alembic Pharmaceuticals get USFDA approval for? | ✅ | ✅ | ✅ | lookup | answered |
| 4 | factual | Tell me about the Waaree Energies battery plant | ✅ | ✅ | ✅ | lookup | answered |
| 5 | factual | What order did Texmaco Rail receive? | ✅ | ✅ | ✅ | lookup | answered |
| 6 | factual (common word) | What order did Texmaco Rail receive and what is its value? | ✅ | ✅ | ✅ | lookup | answered |
| 7 | factual | What is Zee Entertainment doing with its buyback? | ✅ | ✅ | ✅ | lookup | answered |
| 8 | factual | 5paisa acquisition update | ✅ | ✅ | ✅ | lookup | answered |
| 9 | factual (ticker) | KAYNES joint venture | ✅ | ✅ | ✅ | lookup | answered |
| 10 | factual (typo) | What did Kaynes Technolgy announce? | ✅ | ✅ | ✅ | lookup | answered |
| 11 | list | Which companies declared a dividend this week? | ❌ | ❌ | ✅ | list (metadata filter) | answered |
| 12 | list | List all buyback announcements | ❌ | ❌ | ✅ | list (metadata filter) | answered |
| 13 | list | Which companies announced a stock split? | ❌ | ❌ | ✅ | list (metadata filter) | answered |
| 14 | list | Which companies received new orders or contracts? | ❌ | ❌ | ✅ | list (metadata filter) | answered |
| 15 | list | Any open offers filed this week? | ✅ | ✅ | ✅ | lookup | answered |
| 16 | top | What were the most important filings yesterday? | ❌ | ❌ | ✅ | top (ranked by importance score) | answered |
| 17 | list + date | Which companies had credit rating updates on 14 Nov? | ❌ | ❌ | ✅ | list (metadata filter) | answered |
| 18 | compare | Compare the announcements of Dhampur Bio Organics and Zee Entertainment | ✅ | ✅ | ✅ | compare (query decomposition) | answered |
| 19 | compare | Compare Alembic Pharmaceuticals and Wanbury approvals | ✅ | ✅ | ✅ | compare (query decomposition) | answered |
| 20 | multi-part | Did Dhampur Bio Organics announce both results and a buyback? | ✅ | ✅ | ✅ | lookup | answered |
| 21 | multi-part | Which companies started new plants or added capacity, and what capacity? | ❌ | ✅ | ✅ | list (metadata filter) | answered |
| 22 | advice | Should I buy Reliance shares now? | ❌ | ❌ | ✅ | advice | refused |
| 23 | advice | What is the target price for Waaree Energies? | ❌ | ❌ | ✅ | advice | refused |
| 24 | unsupported (live data) | What is the current share price of Ashok Leyland? | ❌ | ❌ | ✅ | live_price | refused |
| 25 | out of window | What were Infosys results in 2021? | ❌ | ❌ | ✅ | out_of_window | out_of_window |
| 26 | out of domain | Who won the cricket world cup? | ❌ | ❌ | ✅ | lookup | not_found |
| 27 | out of domain | How do I bake a chocolate cake? | ❌ | ❌ | ✅ | lookup | not_found |
| 28 | not in data | What did Tesla announce this week? | ❌ | ❌ | ✅ | lookup | not_found |
| 29 | brand not in data (typo) | any zomato eaternal filings are there ?? | ❌ | ❌ | ✅ | lookup | not_found |
| 30 | brand not in data | Any Paytm news this week? | ❌ | ❌ | ✅ | lookup | not_found |
| 31 | brand alias | What did TCS announce this week? | ✅ | ✅ | ✅ | lookup | answered |
| 32 | out of domain | Who is Virat Kohli? | ❌ | ❌ | ✅ | lookup | not_found |
