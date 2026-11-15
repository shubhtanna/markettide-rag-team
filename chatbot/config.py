"""All tunable settings in one place, so experiments don't mean hunting through code."""
import os
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data" / "filings_enriched.csv"
FALLBACK_CSV = ROOT / "data" / "filings_last_7_days.csv"
INDEX_DIR = ROOT / "chatbot" / "index"
MODEL_CACHE = ROOT / "chatbot" / ".model_cache"

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

# --- Embeddings -------------------------------------------------------------
# bge-small: 384 dimensions, strong on retrieval benchmarks (MTEB), ~67 MB ONNX
# model run by fastembed, so no PyTorch and it fits on a 512 MB free server.
EMBED_MODEL = "BAAI/bge-small-en-v1.5"
# bge models retrieve better when the *query* (not the documents) carries this prefix.
QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

# --- Chunking ---------------------------------------------------------------
CHUNK_WORDS = 180          # ~240 tokens: one fact-dense paragraph of a filing
CHUNK_OVERLAP = 40         # keeps a number together with the sentence that explains it
MAX_CHUNKS_PER_FILING = 6  # facts sit on the first pages; the tail is mostly annexures

# --- Retrieval --------------------------------------------------------------
DENSE_CANDIDATES = 60
BM25_CANDIDATES = 60
RRF_K = 60                 # standard Reciprocal Rank Fusion constant
TOP_K = 8                  # chunks sent to the LLM
MAX_CHUNKS_PER_DOC = 2     # diversity: stop one long filing filling every slot
LIST_LIMIT = 30            # filings shown for "which companies..." questions
MIN_DENSE_SCORE = 0.65     # calibrated on 20 probes: on-topic >= 0.675, off-topic <= 0.632

# --- Reranker (cross-encoder) ----------------------------------------------
RERANK_MODEL = "Xenova/ms-marco-MiniLM-L-6-v2"
RERANK_POOL = 24
# Off on the free 512 MB server (saves ~85 MB); eval showed 27/27 with or without it.
RERANK_ENABLED = os.getenv("TIDEBOT_RERANK", "1") == "1"

# --- LLM --------------------------------------------------------------------
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GROQ_MODELS = [m.strip() for m in os.getenv(
    "GROQ_MODELS", "llama-3.3-70b-versatile,openai/gpt-oss-120b,llama-3.1-8b-instant").split(",") if m.strip()]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
TEMPERATURE = 0.1

NOT_FOUND = "I could not find this in the last 7 days of NSE filings I have."
DISCLAIMER = "For information only, not investment advice."
