"""
ingest.py - Data Preprocessing & Embedding Indexer for Market Tide
Reads data/filings_last_7_days.csv, builds rich search chunks,
and pre-computes sentence embeddings and BM25 tokenized corpus.
"""

import os
import re
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer
from rank_bm25 import BM25Okapi

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "filings_last_7_days.csv")
CACHE_DIR = os.path.join(BASE_DIR, "chatbot", "cache")

os.makedirs(CACHE_DIR, exist_ok=True)

def tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokenizer for BM25."""
    return re.findall(r"\w+", text.lower())

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize fields, fill missing tickers, and construct rich chunk text."""
    df = df.copy()
    
    # Fill null tickers with company abbreviation
    df['ticker'] = df['ticker'].fillna(df['company'].apply(lambda x: ''.join([w[0] for w in x.split()[:5]]).upper()))
    df['pdf_url'] = df['pdf_url'].fillna('#')
    df['importance_score'] = df['importance_score'].fillna(50).astype(int)
    
    # Build rich search text for every filing
    # Combining ticker, company, category, tag, date, and description for maximum keyword and semantic match
    def make_chunk_text(row):
        ticker_str = f"({row['ticker']})" if pd.notna(row['ticker']) and row['ticker'] else ""
        return (
            f"Date: {row['date']} {row['time']} | Exchange: {row['exchange']} | "
            f"Company: {row['company']} {ticker_str} | "
            f"Category: {row['category']} | Tag: {row['tag']} | Score: {row['importance_score']} | "
            f"Headline: {row['headline']} | "
            f"Details: {row['description']}"
        )
    
    df['search_chunk'] = df.apply(make_chunk_text, axis=1)
    return df

def build_indices(force_recompute: bool = False):
    """Generate or load cached vector embeddings and BM25 index."""
    embeddings_file = os.path.join(CACHE_DIR, "embeddings.npy")
    metadata_file = os.path.join(CACHE_DIR, "metadata.pkl")
    bm25_file = os.path.join(CACHE_DIR, "bm25.pkl")
    
    if not force_recompute and os.path.exists(embeddings_file) and os.path.exists(metadata_file) and os.path.exists(bm25_file):
        print("✓ Loading pre-computed index from cache...")
        embeddings = np.load(embeddings_file)
        with open(metadata_file, "rb") as f:
            metadata_df = pickle.load(f)
        with open(bm25_file, "rb") as f:
            bm25 = pickle.load(f)
        print(f"✓ Cache loaded successfully! ({len(metadata_df)} filings ready)")
        return metadata_df, embeddings, bm25

    print(f"Reading dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)
    df = clean_data(df)
    print(f"Cleaned {len(df)} filings.")

    print("Building BM25 keyword index...")
    tokenized_corpus = [tokenize(doc) for doc in df['search_chunk']]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(bm25_file, "wb") as f:
        pickle.dump(bm25, f)
    print("✓ BM25 index built and cached.")

    print("Loading embedding model (all-MiniLM-L6-v2)...")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    
    print("Computing dense vector embeddings for all 2,766 filings...")
    chunks = df['search_chunk'].tolist()
    embeddings = embedder.encode(chunks, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
    embeddings = np.array(embeddings, dtype=np.float32)

    np.save(embeddings_file, embeddings)
    with open(metadata_file, "wb") as f:
        pickle.dump(df, f)

    print("✓ Vector embeddings saved to cache successfully!")
    return df, embeddings, bm25

if __name__ == "__main__":
    build_indices(force_recompute=True)
