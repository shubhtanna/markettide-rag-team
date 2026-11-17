"""Local RAG API hosted alongside Streamlit for the Spatial UI."""

from __future__ import annotations

import json
import math
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

ALLOWED_ORIGINS = {"http://127.0.0.1:8765", "http://localhost:8765"}
SOURCE_FIELDS = (
    "id", "date", "time", "company", "ticker", "category", "tag",
    "headline", "summary", "description", "importance_score", "pdf_url",
    "page_url",
)
_server = None
_server_lock = threading.Lock()


def _json_safe(value):
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if hasattr(value, "item"):
        try:
            return _json_safe(value.item())
        except (ValueError, TypeError):
            pass
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _handler_for(agent):
    class RAGRequestHandler(BaseHTTPRequestHandler):
        def _send_json(self, status, payload):
            body = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            origin = self.headers.get("Origin", "")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            if origin in ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self):
            if urlsplit(self.path).path != "/api/chat":
                self._send_json(404, {"error": "Endpoint not found."})
                return
            origin = self.headers.get("Origin", "")
            self.send_response(204)
            if origin in ALLOWED_ORIGINS:
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.send_header("Content-Length", "0")
            self.end_headers()

        def do_GET(self):
            if urlsplit(self.path).path == "/api/health":
                self._send_json(200, {"ok": True})
            else:
                self._send_json(404, {"error": "Endpoint not found."})

        def do_POST(self):
            if urlsplit(self.path).path != "/api/chat":
                self._send_json(404, {"error": "Endpoint not found."})
                return
            origin = self.headers.get("Origin", "")
            if origin and origin not in ALLOWED_ORIGINS:
                self._send_json(403, {"error": "This local API only accepts the Market Tide interface."})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size <= 0 or size > 16_384:
                    self._send_json(400, {"error": "Please send a shorter question."})
                    return
                payload = json.loads(self.rfile.read(size))
                if not isinstance(payload, dict):
                    self._send_json(400, {"error": "The request body must be a JSON object."})
                    return
                query = str(payload.get("query", "")).strip()
                if not query or len(query) > 2_000:
                    self._send_json(400, {"error": "Enter a question up to 2,000 characters."})
                    return
                history = payload.get("history", [])
                if not isinstance(history, list):
                    history = []
                history = [
                    {"role": turn.get("role"), "content": str(turn.get("content", ""))[:2_000]}
                    for turn in history[-6:]
                    if isinstance(turn, dict) and turn.get("role") in {"user", "assistant"}
                ]
                answer_stream, docs, context = agent.stream_response(query, chat_history=history)
                sources = [
                    {field: _json_safe(doc.get(field)) for field in SOURCE_FIELDS if field in doc}
                    for doc in docs
                ]
                self._send_json(200, {
                    "answer": "".join(answer_stream),
                    "sources": sources,
                    "tool_context": context,
                })
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send_json(400, {"error": "The request body must be valid JSON."})
            except Exception as error:
                self.log_error("RAG request failed: %s", error)
                self._send_json(500, {"error": "The filing assistant could not complete that search."})

        def log_message(self, fmt, *args):
            return

    return RAGRequestHandler


def start_background_server(agent):
    """Start the API once in the Streamlit process, safely across reruns."""
    global _server
    if _server is not None:
        return _server
    with _server_lock:
        if _server is None:
            host = os.getenv("MARKETTIDE_API_HOST", "127.0.0.1")
            port = int(os.getenv("MARKETTIDE_API_PORT", "8502"))
            server = ThreadingHTTPServer((host, port), _handler_for(agent))
            server.daemon_threads = True
            threading.Thread(target=server.serve_forever, daemon=True).start()
            _server = server
    return _server
