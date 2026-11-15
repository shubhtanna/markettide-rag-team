"""BM25 (Okapi) keyword search on compact numpy postings.

Same formula as the rank_bm25 library, but rank_bm25 keeps a Python dict per document
(~120 MB for our 10k chunks). Postings in numpy arrays take ~10 MB, which is what lets
the whole app fit in a free 512 MB server.

score(q, d) = sum over query terms t of  idf(t) * tf(t,d) * (k1+1) / (tf(t,d) + k1 * (1 - b + b * |d| / avgdl))
"""
import math
from collections import Counter

import numpy as np


class BM25:
    def __init__(self, tokenized_docs, k1=1.5, b=0.75):
        self.k1, self.b = k1, b
        self.n_docs = len(tokenized_docs)
        lengths = np.array([len(d) for d in tokenized_docs], dtype=np.float32)
        self.avgdl = float(lengths.mean()) if self.n_docs else 0.0
        postings = {}
        for doc_id, toks in enumerate(tokenized_docs):
            for term, tf in Counter(toks).items():
                postings.setdefault(term, ([], []))
                postings[term][0].append(doc_id)
                postings[term][1].append(tf)
        norm = k1 * (1 - b + b * lengths / max(self.avgdl, 1e-9))
        # Okapi idf exactly as rank_bm25: negative idf (words in > half the docs) is
        # replaced by 0.25 x the average idf, so very common words still count a little.
        raw = {t: math.log((self.n_docs - len(ids) + 0.5) / (len(ids) + 0.5)) for t, (ids, _) in postings.items()}
        floor = 0.25 * (sum(raw.values()) / max(len(raw), 1))
        self.idf = {t: (v if v >= 0 else floor) for t, v in raw.items()}
        self.postings = {}
        for term, (ids, tfs) in postings.items():
            ids = np.array(ids, dtype=np.int32)
            tfs = np.array(tfs, dtype=np.float32)
            # pre-compute the tf part so a query is just a few vector additions
            self.postings[term] = (ids, (tfs * (k1 + 1) / (tfs + norm[ids])).astype(np.float32))

    # ------------------------------------------------------------- persistence
    # Built once at ingest time; the server only loads flat arrays (no startup spike).
    def save(self, path):
        terms = list(self.postings)
        offsets = np.zeros(len(terms) + 1, dtype=np.int64)
        for i, t in enumerate(terms):
            offsets[i + 1] = offsets[i] + len(self.postings[t][0])
        ids = np.concatenate([self.postings[t][0] for t in terms]) if terms else np.zeros(0, np.int32)
        w = np.concatenate([self.postings[t][1] for t in terms]) if terms else np.zeros(0, np.float32)
        idf = np.array([self.idf[t] for t in terms], dtype=np.float32)
        np.savez_compressed(path, terms=np.array(terms), offsets=offsets, ids=ids, w=w, idf=idf,
                            n_docs=np.array([self.n_docs]))

    @classmethod
    def load(cls, path):
        z = np.load(path)
        self = cls.__new__(cls)
        self.n_docs = int(z["n_docs"][0])
        terms, offsets, ids, w, idf = z["terms"].tolist(), z["offsets"], z["ids"], z["w"], z["idf"]
        self.idf = dict(zip(terms, idf.tolist()))
        self.postings = {t: (ids[offsets[i]:offsets[i + 1]], w[offsets[i]:offsets[i + 1]])
                         for i, t in enumerate(terms)}
        return self

    def get_scores(self, query_tokens):
        scores = np.zeros(self.n_docs, dtype=np.float32)
        for t in query_tokens:
            p = self.postings.get(t)
            if p is not None:
                scores[p[0]] += self.idf[t] * p[1]
        return scores
