"""Step 1 of the pipeline: data -> clean -> chunks -> embeddings -> FAISS vector store.

    python chatbot/ingest.py

Writes chatbot/index/: filings.json, chunks.json, vectors.faiss, manifest.json
"""
import json
import re
import sys
import time

import faiss
import numpy as np
import pandas as pd

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import config  # noqa: E402
from embedder import embed_documents  # noqa: E402

JUNK_BODY = re.compile(r"^\W*$")


def load_filings():
    path = config.DATA_CSV if config.DATA_CSV.exists() else config.FALLBACK_CSV
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    n0 = len(df)
    if "body" not in df:
        df["body"] = ""
    df = df[df["headline"].str.strip() != ""]
    df = df.drop_duplicates(subset=["id"])
    # Same company + same headline on the same day = the same filing uploaded twice.
    df = df.drop_duplicates(subset=["company", "date", "headline"])
    df["importance_score"] = pd.to_numeric(df["importance_score"], errors="coerce").fillna(0).astype(int)
    df["body"] = df["body"].fillna("").map(lambda b: "" if JUNK_BODY.match(b) else b)
    df = df.sort_values(["date", "time"], ascending=False).reset_index(drop=True)
    print(f"loaded {path.name}: {n0} rows -> {len(df)} after cleaning; "
          f"{(df.body.str.len() > 0).sum()} have PDF text")
    return df


def header(r):
    """Contextual chunk header: every chunk says which filing it came from.

    Without it, a chunk like "Revenue up 18% to Rs 1,240 crore" has no company or
    date, so neither the vector search nor BM25 can link it to the question
    "What were Infosys's results?".
    """
    return (f"{r['company']} ({r['ticker']}) | {r['date']} | {r['tag']} | {r['category']}\n"
            f"Headline: {r['headline']}")


def split_words(text, size, overlap):
    words = text.split()
    if not words:
        return []
    out, step = [], size - overlap
    for start in range(0, len(words), step):
        out.append(" ".join(words[start:start + size]))
        if start + size >= len(words):
            break
    return out


def build_chunks(df):
    chunks = []
    for i, r in df.iterrows():
        h = header(r)
        pieces = split_words(r["body"], config.CHUNK_WORDS, config.CHUNK_OVERLAP)[:config.MAX_CHUNKS_PER_FILING]
        if not pieces:
            pieces = [""]
        for j, p in enumerate(pieces):
            chunks.append({"doc": int(i), "part": j, "text": (h + ("\n" + p if p else "")).strip()})
    return chunks


def main():
    t = time.time()
    config.INDEX_DIR.mkdir(parents=True, exist_ok=True)
    df = load_filings()
    chunks = build_chunks(df)
    print(f"{len(chunks)} chunks from {len(df)} filings "
          f"(avg {len(chunks) / max(len(df), 1):.1f} per filing)")

    vecs = embed_documents([c["text"] for c in chunks])
    vecs = np.asarray(vecs, dtype="float32")
    faiss.normalize_L2(vecs)                       # cosine similarity == inner product
    index = faiss.IndexFlatIP(vecs.shape[1])       # exact search: 15k vectors is tiny
    index.add(vecs)
    faiss.write_index(index, str(config.INDEX_DIR / "vectors.faiss"))

    cols = ["id", "date", "time", "exchange", "company", "ticker", "category", "tag",
            "importance_score", "headline", "body", "pdf_url", "page_url"]
    df[cols].to_json(config.INDEX_DIR / "filings.json", orient="records", force_ascii=False)
    (config.INDEX_DIR / "chunks.json").write_text(json.dumps(chunks, ensure_ascii=False), encoding="utf-8")
    manifest = {
        "filings": len(df), "chunks": len(chunks), "embed_model": config.EMBED_MODEL,
        "dim": int(vecs.shape[1]), "date_from": df["date"].min(), "date_to": df["date"].max(),
        "chunk_words": config.CHUNK_WORDS, "chunk_overlap": config.CHUNK_OVERLAP,
        "with_pdf_text": int((df.body.str.len() > 0).sum()),
    }
    (config.INDEX_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"index written in {time.time() - t:.0f}s: {manifest}")


if __name__ == "__main__":
    main()
