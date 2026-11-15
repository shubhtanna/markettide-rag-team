"""Embedding + reranking models, loaded once and shared.

fastembed runs the models with ONNX Runtime: same quality as sentence-transformers
but no PyTorch, so the app starts fast and fits in a free 512 MB server.
"""
import functools

import numpy as np

import config


@functools.lru_cache(maxsize=1)
def _model():
    from fastembed import TextEmbedding
    return TextEmbedding(config.EMBED_MODEL, cache_dir=str(config.MODEL_CACHE))


def embed_documents(texts, batch_size=64):
    return np.array(list(_model().embed(texts, batch_size=batch_size)), dtype="float32")


def embed_query(text):
    v = np.array(list(_model().embed([config.QUERY_PREFIX + text])), dtype="float32")
    return v / np.linalg.norm(v, axis=1, keepdims=True)


@functools.lru_cache(maxsize=1)
def _reranker():
    from fastembed.rerank.cross_encoder import TextCrossEncoder
    return TextCrossEncoder(config.RERANK_MODEL, cache_dir=str(config.MODEL_CACHE))


def rerank_scores(query, texts):
    """Cross-encoder reads query and chunk *together*, so it judges relevance far
    better than comparing two separate vectors. Too slow for 15k chunks, perfect
    for re-ordering the top ~24."""
    return list(_reranker().rerank(query, texts))


def warm_up(rerank=True):
    embed_query("warm up")
    if rerank:
        try:
            rerank_scores("warm up", ["warm up"])
        except Exception:
            pass
