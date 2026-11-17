"""
tools.py - Structured Data Tools for Market Tide
Implements deterministic, multi-word company/ticker resolution and hybrid retrieval.
"""

import os
import re
import pandas as pd
import numpy as np

try:
    from .retriever import HybridRetriever
except ImportError:
    from retriever import HybridRetriever

STOPWORDS = set([
    'did', 'file', 'anything', 'in', 'the', 'last', '7', 'days', 'what', 'about',
    'share', 'shares', 'stock', 'stocks', 'announcements', 'announcement', 'filing',
    'filings', 'company', 'companies', 'any', 'this', 'week', 'today', 'yesterday',
    'please', 'tell', 'me', 'show', 'list', 'is', 'there', 'who', 'which', 'when',
    'where', 'how', 'why', 'are', 'was', 'were', 'give'
])

# Ordinary dictionary words, names, trivia terms, or generic words that must NEVER
# be used for loose single-word company resolution.
DISALLOWED_SINGLE_WORDS = {
    # Specifically required exclusions:
    "swift", "world", "modi", "shah", "prime", "delhi", "ipl", "learning", "market", "tea", "chip", "india",
    # Additional generic / dictionary / celebrity / geographical words:
    "impact", "social", "significant", "filing", "filings", "announcement", "announcements",
    "power", "energy", "industries", "industry", "limited", "enterprises", "enterprise",
    "finance", "capital", "infra", "infrastructure", "holdings", "holding", "services",
    "service", "system", "systems", "solutions", "solution", "tech", "technology",
    "technologies", "media", "sun", "star", "city", "care", "global", "international",
    "group", "corp", "corporation", "bank", "life", "motor", "motors", "steel",
    "oil", "gas", "air", "food", "foods", "auto", "labs", "lab", "pharma", "green",
    "smart", "digital", "real", "estate", "housing", "hotel", "hotels", "hospital",
    "hospitals", "park", "road", "rail", "express", "space", "line", "lines", "net",
    "network", "networks", "trade", "trading", "trust", "venture", "ventures",
    "security", "securities", "development", "properties", "engineering", "consultancy",
    "logistics", "shipping", "minerals", "metals", "chemicals", "agency", "agencies",
    "micro", "nano", "bio", "premier", "first", "best", "super", "universal",
    "national", "state", "apex", "royal", "golden", "orient", "western", "eastern",
    "southern", "northern", "central", "union", "standard", "classic", "modern",
    "future", "dynamic", "advance", "advanced", "discovery", "vision", "growth",
    "value", "blue", "white", "black", "red", "gold", "silver", "weather", "match",
    "score", "capital", "president", "minister", "recipe", "cookies", "bake", "cake",
    "coffee", "movie", "movies", "actor", "actress", "song", "songs", "cricket",
    "football", "tennis", "sports", "python", "code", "coding", "algorithm",
    "science", "temperature", "who", "what", "where", "when", "why", "how",
    "general", "news", "latest", "update", "updates",
    # Hardened against polysemous tickers and dictionary nouns/verbs:
    "titan", "idea", "crown", "point", "clean", "diamond", "force", "time", "drive",
    "solve", "federal", "hero", "target", "focus", "speed", "deep", "bright", "gem",
    "sky", "moon", "date", "bombay", "nice", "celebrity", "singer", "film", "films",
    "vehicle", "vehicles", "delivery", "report", "reports",
    # Everyday filing vocabulary that is also a ticker or a company's first word ("premium" -> Premium Plast)
    "premium", "offer", "offers", "price", "prices", "record", "result", "results", "profit", "profits",
    "order", "orders", "rating", "ratings", "approval", "approvals", "plant", "capacity", "rights", "issue",
    "fund", "funds", "merger", "scheme", "board", "meeting", "quarter", "quarterly", "annual", "interim",
    "final", "equity", "debt", "loan", "credit", "share", "shares", "buyback", "bonus", "split", "dividend",
    "acquisition", "stake", "promoter", "revenue", "margin", "growth", "outlook"
}

# Explicit corporate indicators that confirm a financial/equity context
CORPORATE_INDICATORS = {
    "stock", "stocks", "share", "shares", "filing", "filings", "announcement",
    "announcements", "ltd", "limited", "corp", "corporation", "inc", "company",
    "co", "nse", "bse", "board", "dividend", "q1", "q2", "q3", "q4", "fy26",
    "fy27", "earnings", "results", "order", "orders", "agm", "egm",
    "announce", "announced", "disclose", "disclosed", "disclosure", "disclosures",
    "file", "filed", "report", "reports", "reported", "buyback", "buybacks", "bonus"
}

# Major NSE listed companies (including those with 0 filings in the Nov 9-15 window)
MAJOR_NSE_COMPANIES = [
    {"ticker": "ZEEL", "company": "Zee Entertainment Enterprises Limited", "aliases": ["zee entertainment", "zeel", "zee"]},
    {"ticker": "INFY", "company": "Infosys Limited", "aliases": ["infosys", "infy", "infosys limited"]},
    {"ticker": "WIPRO", "company": "Wipro Limited", "aliases": ["wipro", "wipro limited"]},
    {"ticker": "ICICIBANK", "company": "ICICI Bank Limited", "aliases": ["icici bank", "icicibank", "icici bank limited", "icici"]},
    {"ticker": "ITC", "company": "ITC Limited", "aliases": ["itc limited", "itc"]},
    {"ticker": "HCLTECH", "company": "HCL Technologies Limited", "aliases": ["hcl tech", "hcltech", "hcl technologies"]},
    {"ticker": "SUNPHARMA", "company": "Sun Pharmaceutical Industries Limited", "aliases": ["sun pharma", "sunpharma"]},
    {"ticker": "NTPC", "company": "NTPC Limited", "aliases": ["ntpc limited", "ntpc"]},
    {"ticker": "ADANIPORTS", "company": "Adani Ports and Special Economic Zone Limited", "aliases": ["adani ports", "adani port", "adaniports"]},
    {"ticker": "COALINDIA", "company": "Coal India Limited", "aliases": ["coal india", "coalindia"]},
    {"ticker": "TATAMOTORS", "company": "Tata Motors Limited", "aliases": ["tata motors", "tatamotors"]},
    {"ticker": "BAJAJ-AUTO", "company": "Bajaj Auto Limited", "aliases": ["bajaj auto"]},
    {"ticker": "NESTLEIND", "company": "Nestle India Limited", "aliases": ["nestle india", "nestle"]},
    {"ticker": "TECHM", "company": "Tech Mahindra Limited", "aliases": ["tech mahindra", "techm"]},
    {"ticker": "ULTRACEMCO", "company": "UltraTech Cement Limited", "aliases": ["ultratech cement", "ultratech"]},
    {"ticker": "GRASIM", "company": "Grasim Industries Limited", "aliases": ["grasim", "grasim industries"]},
    {"ticker": "CIPLA", "company": "Cipla Limited", "aliases": ["cipla limited", "cipla"]},
    {"ticker": "DRREDDY", "company": "Dr. Reddy Laboratories Limited", "aliases": ["dr reddy", "dr reddys", "drreddy"]},
    {"ticker": "SBIN", "company": "State Bank of India", "aliases": ["state bank of india", "state bank", "sbin", "sbi"]}
]


class MarketTools:
    def __init__(self):
        self.retriever = HybridRetriever(force_recompute=False)
        self.df = self.retriever.metadata_df
        self._build_company_phrase_index()

    def _build_company_phrase_index(self):
        """Pre-index multi-word company phrases for deterministic O(1) phrase matching."""
        self.phrase_to_comps = {}
        comps = self.df[['ticker', 'company']].drop_duplicates()
        for _, row in comps.iterrows():
            ticker, comp = row['ticker'], row['company']
            for p in self._get_company_phrases(comp):
                if p not in self.phrase_to_comps:
                    self.phrase_to_comps[p] = []
                self.phrase_to_comps[p].append((ticker, comp))
        self.sorted_phrases = sorted(self.phrase_to_comps.keys(), key=lambda x: len(x), reverse=True)

    @staticmethod
    def _get_company_phrases(company_name: str) -> list[str]:
        c = company_name.lower()
        c_clean = re.sub(r'\b(limited|ltd\.?|corp\.?|corporation|inc\.?|llp|pvt\.?)\b.*$', '', c).strip()
        c_clean = re.sub(r'[\(\)\[\],]', ' ', c_clean).strip()
        c_clean = re.sub(r'\s+', ' ', c_clean).strip()
        
        phrases = []
        if c_clean and len(c_clean.split()) >= 2:
            phrases.append(c_clean)
            if c_clean.startswith('the '):
                phrases.append(c_clean[4:].strip())
            tokens = [w for w in c_clean.split() if w]
            if len(tokens) >= 2:
                phrases.append(' '.join(tokens[:2]))
            if len(tokens) >= 3:
                phrases.append(' '.join(tokens[:3]))
        return [p for p in set(phrases) if len(p.split()) >= 2 and len(p) >= 5]

    def resolve_company(self, query: str) -> list[dict]:
        """
        Resolve company name or ticker symbol using deterministic multi-stage matching:
        1. Exact multi-word company phrase match (handles State Bank of India, Federal Bank, etc.)
        2. Known Major NSE companies (handles zero-filing giants e.g. Infosys, Wipro)
        3. Exact ticker check (disallowed words require corporate indicators or pure ticker query)
        4. Multi-word pair search
        5. Fallback single word match (requires corporate indicator or pure query)
        """
        raw_words = re.findall(r'[a-zA-Z0-9]+', query.lower())
        words = [w for w in raw_words if w not in STOPWORDS and len(w) >= 3]
        if not words:
            return []

        q_lower = query.lower()
        has_corp_indicator = (
            any(w in CORPORATE_INDICATORS for w in raw_words) or
            ("nse:" in q_lower or "bse:" in q_lower)
        )
        is_exact_ticker_query = (len(words) == 1 and len(raw_words) <= 2)

        # 1. Exact Multi-Word Phrase Matching against Company Names (State Bank of India, etc.)
        for p in self.sorted_phrases:
            if re.search(r'\b' + re.escape(p) + r'\b', q_lower):
                candidates = self.phrase_to_comps[p]
                summary = []
                for ticker, comp in candidates:
                    count = len(self.df[self.df['ticker'] == ticker])
                    summary.append({"ticker": ticker, "company": comp, "count": count})
                return sorted(summary, key=lambda x: x['count'], reverse=True)

        # 2. Known Major NSE Companies (including zero-filing companies like Infosys, Wipro, etc.)
        for comp in MAJOR_NSE_COMPANIES:
            for alias in comp["aliases"]:
                if re.search(r'\b' + re.escape(alias) + r'\b', q_lower):
                    exact_in_df = self.df[self.df['ticker'].str.upper() == comp["ticker"]]
                    count = len(exact_in_df)
                    comp_name = exact_in_df.iloc[0]['company'] if count > 0 else comp["company"]
                    return [{"ticker": comp["ticker"], "company": comp_name, "count": count}]

        # 3. Exact ticker check
        for w in words:
            w_upper = w.upper()
            if w in DISALLOWED_SINGLE_WORDS and not (has_corp_indicator or f"nse:{w}" in q_lower or f"bse:{w}" in q_lower):
                continue
            # A common word ("premium", "order") only counts as a ticker when written like one: in capitals,
            # with an NSE:/BSE: prefix, or as the whole query. Otherwise "Zee's buyback premium" became Premium Plast.
            if w in DISALLOWED_SINGLE_WORDS and not (re.search(r"\b" + re.escape(w_upper) + r"\b", query)
                                                     or f"nse:{w}" in q_lower or f"bse:{w}" in q_lower
                                                     or is_exact_ticker_query):
                continue
            exact_ticker = self.df[self.df['ticker'].str.upper() == w_upper]
            if not exact_ticker.empty:
                return [{
                    "ticker": w_upper,
                    "company": exact_ticker.iloc[0]['company'],
                    "count": len(exact_ticker)
                }]

        # 4. Multi-word pair search
        if len(words) >= 2:
            for i in range(len(words)):
                for j in range(i + 1, len(words)):
                    w1, w2 = words[i], words[j]
                    if w1 in DISALLOWED_SINGLE_WORDS and w2 in DISALLOWED_SINGLE_WORDS and not has_corp_indicator:
                        continue
                    mask = (
                        self.df['company'].str.lower().str.contains(r'\b' + re.escape(w1) + r'\b', regex=True, na=False) &
                        self.df['company'].str.lower().str.contains(r'\b' + re.escape(w2) + r'\b', regex=True, na=False)
                    )
                    m = self.df[mask]
                    if not m.empty:
                        summary = []
                        for ticker, group in m.groupby('ticker'):
                            summary.append({
                                "ticker": ticker,
                                "company": group.iloc[0]['company'],
                                "count": len(group)
                            })
                        return sorted(summary, key=lambda x: x['count'], reverse=True)

        # 5. Fallback single word match ONLY IF distinctive, NOT in disallowed list, and either corp indicator or pure query
        distinctive_words = [w for w in words if w not in DISALLOWED_SINGLE_WORDS and len(w) >= 4]
        if distinctive_words and (has_corp_indicator or len(words) == 1):
            for w in distinctive_words:
                matches = self.df[
                    self.df['company'].str.lower().str.contains(r'\b' + re.escape(w) + r'\b', regex=True, na=False) |
                    (self.df['ticker'].str.lower() == w)
                ]
                if not matches.empty:
                    summary = []
                    for ticker, group in matches.groupby('ticker'):
                        summary.append({
                            "ticker": ticker,
                            "company": group.iloc[0]['company'],
                            "count": len(group)
                        })
                    return sorted(summary, key=lambda x: x['count'], reverse=True)[:15]

        return []

    def get_company_filings(self, ticker: str, top_k: int = 5) -> list[dict]:
        """Fetch all official filings for a specific confirmed ticker."""
        ticker_clean = ticker.strip().upper()
        filings = self.df[self.df['ticker'].str.upper() == ticker_clean].sort_values(
            by=['importance_score', 'date'], ascending=[False, False]
        ).head(top_k)
        return filings.to_dict(orient='records')

    def filter_by_category(self, tag_or_category: str, min_score: int = 45, top_k: int = 6) -> list[dict]:
        """Deterministic retrieval of filings filtered by category tag (e.g. Buyback, Dividend, Results, Order)."""
        tag_clean = tag_or_category.strip().lower()
        matches = self.df[
            (self.df['tag'].str.lower().str.contains(tag_clean, na=False)) |
            (self.df['category'].str.lower().str.contains(tag_clean, na=False))
        ]
        if min_score:
            matches = matches[matches['importance_score'] >= min_score]
        sorted_matches = matches.sort_values(by=['importance_score', 'date'], ascending=[False, False]).head(top_k)
        return sorted_matches.to_dict(orient='records')

    def compare_two_companies(self, company_a: str, company_b: str, top_k: int = 3) -> dict:
        """Query decomposition: retrieve evidence for two companies independently."""
        resolved_a = self.resolve_company(company_a)
        resolved_b = self.resolve_company(company_b)
        docs_a = self.get_company_filings(resolved_a[0]["ticker"], top_k=top_k) if resolved_a else []
        docs_b = self.get_company_filings(resolved_b[0]["ticker"], top_k=top_k) if resolved_b else []
        return {
            "company_a": {"name": company_a, "resolved": resolved_a, "filings": docs_a},
            "company_b": {"name": company_b, "resolved": resolved_b, "filings": docs_b}
        }

    def get_top_high_impact(self, top_k: int = 5) -> list[dict]:
        """Retrieve highest scored filings across the 7-day window."""
        top_df = self.df.sort_values(by=['importance_score', 'date'], ascending=[False, False]).head(top_k)
        return top_df.to_dict(orient='records')

    def hybrid_search(self, query: str, top_k: int = 6, use_hybrid: bool = True) -> list[dict]:
        """General hybrid search with relevance threshold cut-off."""
        return self.retriever.retrieve(query, top_k=top_k, use_hybrid=use_hybrid)
