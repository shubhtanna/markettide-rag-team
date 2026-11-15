"""Run at build time so the server doesn't download models on its first request."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from embedder import warm_up  # noqa: E402

warm_up(rerank=True)
print("models ready")
