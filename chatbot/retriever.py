"""
retriever.py - Hybrid Retrieval Engine for Market Tide
Implements BM25 Keyword Search, Dense Vector Search, and Reciprocal Rank Fusion (RRF),
with exact date, category, and ticker metadata filters.
"""

import os
import re
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

try:
    from .ingest import build_indices, tokenize
except ImportError:
    from ingest import build_indices, tokenize

BM25_STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
    'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a',
    'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
    'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
    'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'don', 'should', "should've", 'now',
    'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', 'couldn', 'didn', 'doesn',
    'hadn', 'hasn', 'haven', 'isn', 'ma', 'mightn', 'mustn', 'needn', 'shan', 'shouldn',
    'wasn', 'weren', 'won', 'wouldn', 'tell', 'me', 'please', 'give', 'show', 'list',
    'announcements', 'announcement', 'filings', 'filing', 'limited', 'ltd', 'company', 'companies',
    # Expanded disclosure verbs & regulatory boilerplate
    'announce', 'announces', 'announced', 'announcing',
    'file', 'files', 'filed',
    'disclosure', 'disclosures', 'disclosed',
    'intimation', 'intimated', 'inform', 'informed', 'informing',
    'report', 'reports', 'reported', 'reporting',
    'submit', 'submits', 'submitted', 'submitting',
    'press', 'conference', 'release', 'releases',
    'agreement', 'agreements',
    'exchange', 'exchanges', 'dated', 'regarding', 'pursuant', 'regulation', 'regulations',
    'corp', 'corporation', 'inc', 'incorporated', 'co'
}

GENERIC_FINANCIAL_WORDS = {
    'quarterly', 'annual', 'financial', 'results', 'audited', 'unaudited',
    'dividend', 'dividends', 'interim', 'final', 'bonus', 'rights', 'issue',
    'buyback', 'buybacks', 'shares', 'share', 'equity', 'debt',
    'order', 'orders', 'contract', 'contracts', 'win', 'wins', 'won', 'award', 'awarded',
    'management', 'director', 'resignation', 'appointment', 'appointed', 'resigned',
    'ceo', 'cfo', 'md', 'kmp', 'executive',
    'meeting', 'board', 'outcome', 'concall', 'earnings', 'call', 'transcript',
    'investor', 'analyst', 'presentation', 'audio', 'recording',
    'acquisition', 'merger', 'demerger', 'amalgamation', 'stake', 'jv', 'joint', 'venture',
    'rating', 'credit', 'care', 'crisil', 'icra', 'reaffirmation',
    'notice', 'update', 'updates', 'intimation', 'disclosure', 'disclosures',
    'loss', 'profit', 'pat', 'ebitda', 'revenue', 'income', 'sales', 'margin',
    'high', 'impact', 'news', 'recent', 'latest', 'today', 'week', 'days', 'day', 'past'
}

class HybridRetriever:
    def __init__(self, force_recompute: bool = False):
        self.metadata_df, self.embeddings, self.bm25 = build_indices(force_recompute=force_recompute)
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        self.num_docs = len(self.metadata_df)

    def dense_search(self, query: str, top_k: int = 20, candidate_indices: np.ndarray = None) -> list[tuple[int, float]]:
        """Vector similarity search using dot product on normalized embeddings."""
        query_vec = self.embedder.encode(query, normalize_embeddings=True)
        if candidate_indices is not None and len(candidate_indices) > 0:
            sub_embeddings = self.embeddings[candidate_indices]
            sims = np.dot(sub_embeddings, query_vec)
            top_sub_idx = np.argsort(sims)[::-1][:top_k]
            return [(candidate_indices[idx], float(sims[idx])) for idx in top_sub_idx]
        else:
            sims = np.dot(self.embeddings, query_vec)
            top_idx = np.argsort(sims)[::-1][:top_k]
            return [(idx, float(sims[idx])) for idx in top_idx]

    def bm25_search(self, query: str, top_k: int = 20, candidate_indices: np.ndarray = None) -> list[tuple[int, float]]:
        """Lexical BM25 keyword search with stopword filtering and plural lemmatization."""
        raw_tokens = tokenize(query)
        query_tokens = []
        for tok in raw_tokens:
            if tok not in BM25_STOPWORDS and len(tok) >= 2:
                query_tokens.append(tok)
                # Expand plural nouns to singular (e.g. buybacks -> buyback)
                if tok.endswith('s') and len(tok) > 3:
                    singular = tok[:-1]
                    if singular not in BM25_STOPWORDS and singular not in query_tokens:
                        query_tokens.append(singular)
        if not query_tokens:
            return []
        
        scores = self.bm25.get_scores(query_tokens)
        if candidate_indices is not None and len(candidate_indices) > 0:
            sub_scores = scores[candidate_indices]
            top_sub_idx = np.argsort(sub_scores)[::-1][:top_k]
            return [(candidate_indices[idx], float(sub_scores[idx])) for idx in top_sub_idx if sub_scores[idx] > 0]
        else:
            top_idx = np.argsort(scores)[::-1][:top_k]
            return [(idx, float(scores[idx])) for idx in top_idx if scores[idx] > 0]

    def rrf_merge(self, dense_results: list[tuple[int, float]], bm25_results: list[tuple[int, float]], k: int = 60) -> list[tuple[int, float]]:
        """Reciprocal Rank Fusion merging dense and BM25 rankings."""
        rrf_scores = {}
        
        for rank, (doc_id, _) in enumerate(dense_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))
            
        for rank, (doc_id, _) in enumerate(bm25_results):
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (k + rank + 1))

        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_docs

    def retrieve(
        self,
        query: str,
        top_k: int = 6,
        use_hybrid: bool = True,
        start_date: str = None,
        end_date: str = None,
        tags: list[str] = None,
        min_score: int = None,
        ticker: str = None,
    ) -> list[dict]:
        """
        Execute filtered hybrid or vector-only retrieval.
        Returns list of structured document dictionaries.
        Enforces calibrated relevance thresholds, grounded lexical requirements,
        and multi-word query term coverage to eliminate noise and out-of-domain retrievals.
        """
        # Extract meaningful content tokens for gating
        raw_tokens = tokenize(query)
        content_tokens = [tok for tok in raw_tokens if tok not in BM25_STOPWORDS and len(tok) >= 2]
        
        # 1. Unconditionally reject queries devoid of content keywords
        if not content_tokens:
            return []

        # Apply metadata filtering mask
        mask = pd.Series(True, index=self.metadata_df.index)
        
        if start_date:
            mask = mask & (self.metadata_df['date'] >= start_date)
        if end_date:
            mask = mask & (self.metadata_df['date'] <= end_date)
        if tags and len(tags) > 0:
            mask = mask & (self.metadata_df['tag'].isin(tags))
        if min_score is not None:
            mask = mask & (self.metadata_df['importance_score'] >= min_score)
        if ticker:
            ticker_clean = ticker.strip().upper()
            mask = mask & (self.metadata_df['ticker'].str.upper() == ticker_clean)

        candidate_indices = np.where(mask.values)[0]
        if len(candidate_indices) == 0:
            return []

        if use_hybrid:
            dense_res = self.dense_search(query, top_k=top_k * 3, candidate_indices=candidate_indices)
            bm25_res = self.bm25_search(query, top_k=top_k * 3, candidate_indices=candidate_indices)
            
            top_dense_score = dense_res[0][1] if dense_res else 0.0
            top_bm25_score = bm25_res[0][1] if bm25_res else 0.0
            
            # 2. Reject unconditionally if dense similarity is below noise floor (0.35)
            if top_dense_score < 0.35:
                return []
            
            # 3. Grounded Lexical Requirement:
            # If BM25 yields 0.0, none of the query's content keywords exist in the corpus.
            # Dense search alone on zero-filing entities (e.g. "What did Infosys announce?")
            # has high cosine similarity (0.52+) with generic corporate announcements.
            # Dense search CANNOT be allowed to retrieve unrelated filings when lexical match is 0.0.
            if not bm25_res or top_bm25_score <= 0.0:
                return []
            
            # 4. Multi-word term coverage check:
            # Prevent single-word accidental matches on out-of-domain queries (e.g., "gold" in "Neeraj Chopra Olympic javelin gold").
            # Require at least 50% term coverage or at least 2 distinctive tokens matching in candidate documents.
            if len(content_tokens) >= 2:
                candidate_doc_indices = [idx for idx, _ in (bm25_res[:3] + dense_res[:3])]
                has_sufficient_coverage = False
                for doc_idx in candidate_doc_indices:
                    doc_row = self.metadata_df.iloc[doc_idx]
                    doc_tokens = set(tokenize(doc_row['search_chunk']))
                    matched_count = sum(
                        1 for t in content_tokens
                        if t in doc_tokens or (t.endswith('s') and t[:-1] in doc_tokens)
                    )
                    coverage = matched_count / len(content_tokens)
                    if coverage >= 0.50 or matched_count >= 2:
                        has_sufficient_coverage = True
                        break
                if not has_sufficient_coverage:
                    return []
            
            # 5. Dual relevance threshold:
            # If dense similarity is in [0.35, 0.42), require stronger BM25 keyword score (>= 10.0)
            if top_dense_score < 0.42 and top_bm25_score < 10.0:
                return []

            # 6. Distinctive Subject / Entity Keyword Grounding:
            # If the user's query specifies entity/subject terms (words not in generic financial categories),
            # candidate filings MUST match at least one subject token. Never return other companies' filings!
            subject_tokens = [tok for tok in content_tokens if tok not in GENERIC_FINANCIAL_WORDS]
            if subject_tokens:
                candidate_doc_indices = [idx for idx, _ in (bm25_res[:5] + dense_res[:5])]
                has_subject_match = False
                for doc_idx in candidate_doc_indices:
                    doc_row = self.metadata_df.iloc[doc_idx]
                    doc_tokens = set(tokenize(doc_row['search_chunk']))
                    if any(st in doc_tokens or (st.endswith('s') and st[:-1] in doc_tokens) for st in subject_tokens):
                        has_subject_match = True
                        break
                if not has_subject_match:
                    return []

            merged = self.rrf_merge(dense_res, bm25_res, k=60)[:top_k]
            ranked_indices = [idx for idx, _ in merged]

            # Filter ranked indices: if subject tokens were specified, prune any document lacking all subject tokens
            if subject_tokens:
                filtered_ranked = []
                for idx in ranked_indices:
                    doc_row = self.metadata_df.iloc[idx]
                    doc_tokens = set(tokenize(doc_row['search_chunk']))
                    if any(st in doc_tokens or (st.endswith('s') and st[:-1] in doc_tokens) for st in subject_tokens):
                        filtered_ranked.append(idx)
                ranked_indices = filtered_ranked
                if not ranked_indices:
                    return []
        else:
            dense_res = self.dense_search(query, top_k=top_k, candidate_indices=candidate_indices)
            top_dense_score = dense_res[0][1] if dense_res else 0.0
            if top_dense_score < 0.42:
                return []
            ranked_indices = [idx for idx, _ in dense_res]

        results = []
        for rank, idx in enumerate(ranked_indices):
            row = self.metadata_df.iloc[idx].to_dict()
            row['rank'] = rank + 1
            results.append(row)
            
        return results

    def format_context(self, docs: list[dict]) -> str:
        """Format retrieved documents into a clean LLM context block."""
        if not docs:
            return "No matching filings found in the 7-day dataset (Nov 9 to Nov 15, 2026)."
            
        context_parts = []
        for d in docs:
            snippet = (
                f"[{d.get('rank', '-')}] COMPANY: {d.get('company')} ({d.get('ticker')})\n"
                f"DATE: {d.get('date')} | CATEGORY: {d.get('category')} | IMPORTANCE: {d.get('importance_score', 'N/A')}/100\n"
                f"HEADLINE: {d.get('headline')}\n"
                f"SUMMARY: {d.get('summary')}\n"
                f"METRICS / DATA: {d.get('extracted_metrics', 'None')}\n"
                f"SOURCE FILING: {d.get('pdf_name', 'Official NSE Filing')}"
            )
            context_parts.append(snippet)
            
        return "\n\n---\n\n".join(context_parts)
