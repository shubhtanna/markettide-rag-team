"""Step 2: hybrid retrieval = metadata filter -> (FAISS vectors + BM25 keywords) -> RRF -> rerank."""
import datetime as dt
import json
import re

import faiss
import numpy as np

import config
from bm25 import BM25
from embedder import embed_query, rerank_scores
from query_parser import CompanyIndex

STOP = set("""a an and are as at be by for from has have in is it its of on or the to was were will with this that
what which who whom how when where why did does do any all about me tell show give please their they them""".split())


def tokenize(text):
    return [t for t in re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text.lower()) if t not in STOP]


class Store:
    def __init__(self, index_dir=config.INDEX_DIR):
        self.filings = json.loads((index_dir / "filings.json").read_text(encoding="utf-8"))
        self.chunks = json.loads((index_dir / "chunks.json").read_text(encoding="utf-8"))
        self.manifest = json.loads((index_dir / "manifest.json").read_text(encoding="utf-8"))
        self.index = faiss.read_index(str(index_dir / "vectors.faiss"))
        bm25_file = index_dir / "bm25.npz"
        self.bm25 = (BM25.load(bm25_file) if bm25_file.exists()
                     else BM25([tokenize(c["text"]) for c in self.chunks]))
        self.companies = CompanyIndex(self.filings)
        self.anchor = dt.date.fromisoformat(self.manifest["date_to"])
        self.first = dt.date.fromisoformat(self.manifest["date_from"])
        self.doc_chunks = {}
        for i, c in enumerate(self.chunks):
            self.doc_chunks.setdefault(c["doc"], []).append(i)

    # ---------------------------------------------------------------- filters
    def filter_docs(self, date_from=None, date_to=None, companies=None, tags=None):
        names = {c for c, _ in companies} if companies else None
        tagset = set(tags) if tags else None
        out = []
        for i, f in enumerate(self.filings):
            if date_from and f["date"] < date_from:
                continue
            if date_to and f["date"] > date_to:
                continue
            if names is not None and f["company"] not in names:
                continue
            if tagset is not None and f["tag"] not in tagset:
                continue
            out.append(i)
        return out

    def list_filings(self, **flt):
        docs = self.filter_docs(**flt)
        # newest first, then most important first (stable sorts)
        docs.sort(key=lambda i: self.filings[i]["date"] + self.filings[i]["time"], reverse=True)
        docs.sort(key=lambda i: self.filings[i]["importance_score"], reverse=True)
        return docs

    # ---------------------------------------------------------------- search
    def _dense(self, qv, allowed, n):
        if allowed is not None:
            ids = np.array(allowed, dtype="int64")
            if len(ids) <= 2000:
                # small filtered set: exact dot products are instant and exact
                sims = (np.vstack([self.index.reconstruct(int(i)) for i in ids]) @ qv[0])
                order = np.argsort(-sims)[:n]
                return [(int(ids[j]), float(sims[j])) for j in order]
            params = faiss.SearchParameters(sel=faiss.IDSelectorBatch(ids))
            D, I = self.index.search(qv, n, params=params)
        else:
            D, I = self.index.search(qv, n)
        return [(int(i), float(d)) for i, d in zip(I[0], D[0]) if i >= 0]

    def _bm25(self, query, allowed, n):
        toks = tokenize(query)
        if not toks:
            return []
        scores = self.bm25.get_scores(toks)
        if allowed is not None:
            mask = np.full(len(scores), -1.0)
            mask[allowed] = scores[allowed]
            scores = mask
        order = np.argsort(-scores)[:n]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]

    def search(self, query, date_from=None, date_to=None, companies=None, tags=None,
               hybrid=True, rerank=True, k=config.TOP_K):
        allowed = None
        if date_from or date_to or companies or tags:
            docs = self.filter_docs(date_from, date_to, companies, tags)
            allowed = [ci for d in docs for ci in self.doc_chunks.get(d, [])]
            if not allowed:
                return []

        qv = embed_query(query)
        dense = self._dense(qv, allowed, config.DENSE_CANDIDATES)
        sparse = self._bm25(query, allowed, config.BM25_CANDIDATES) if hybrid else []

        # Reciprocal Rank Fusion: score = sum 1/(60 + rank). Uses ranks, not raw
        # scores, so cosine (0-1) and BM25 (0-30) never need to be put on one scale.
        fused = {}
        info = {}
        for rank, (cid, s) in enumerate(dense):
            fused[cid] = fused.get(cid, 0) + 1 / (config.RRF_K + rank + 1)
            info.setdefault(cid, {})["dense"] = s
            info[cid]["dense_rank"] = rank + 1
        for rank, (cid, s) in enumerate(sparse):
            fused[cid] = fused.get(cid, 0) + 1 / (config.RRF_K + rank + 1)
            info.setdefault(cid, {})["bm25"] = s
            info[cid]["bm25_rank"] = rank + 1

        ranked = sorted(fused, key=fused.get, reverse=True)

        # Diversity: at most N chunks from one filing.
        per_doc, pool = {}, []
        for cid in ranked:
            d = self.chunks[cid]["doc"]
            if per_doc.get(d, 0) >= config.MAX_CHUNKS_PER_DOC:
                continue
            per_doc[d] = per_doc.get(d, 0) + 1
            pool.append(cid)
            if len(pool) >= config.RERANK_POOL:
                break

        if rerank and config.RERANK_ENABLED and len(pool) > 1:
            try:
                rs = rerank_scores(query, [self.chunks[c]["text"] for c in pool])
                for c, s in zip(pool, rs):
                    info[c]["rerank"] = float(s)
                pool.sort(key=lambda c: info[c]["rerank"], reverse=True)
            except Exception:
                pass

        hits = []
        for cid in pool[:k]:
            c = self.chunks[cid]
            hits.append({"chunk_id": cid, "doc": c["doc"], "text": c["text"],
                         "filing": self.filings[c["doc"]], "rrf": fused[cid], **info.get(cid, {})})
        return hits

    def best_dense(self, query):
        D, _ = self.index.search(embed_query(query), 1)
        return float(D[0][0])
