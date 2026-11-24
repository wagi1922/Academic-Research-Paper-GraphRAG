#!/usr/bin/env python3
"""
Local embedding service — stdlib only (http.server), no pip install needed.
Serves all-MiniLM-L6-v2 (384-d, L2-normalized) in OpenAI-compatible format.

Endpoints:
  GET  /health
  POST /embed            {"texts": [...]}            -> {"embeddings": [[...], ...]}
  POST /v1/embeddings    OpenAI-compatible           -> {"object":"list","data":[...]}

Run from Cap project root:
  /usr/bin/python3 services/local_embedding_service.py            # foreground
  (systemd user unit guard-embedding.service runs this on boot)
"""
import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("local-embedding")

MODEL_NAME = "all-MiniLM-L6-v2"
HOST, PORT = "127.0.0.1", 8788

model = None
_encode_lock = threading.Lock()  # serialize torch forward passes


def _encode(texts):
    with _encode_lock:
        vecs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return vecs.tolist()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        logger.info(f"{self.client_address[0]} {fmt % args}")

    def _json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if urlparse(self.path).path == "/health":
            self._json({"status": "ok", "model": MODEL_NAME, "loaded": model is not None})
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            length = int(self.headers.get("Content-Length", 0))
            payload = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._json({"error": f"bad request: {e}"}, 400)
            return

        if path == "/embed":
            texts = payload.get("texts", [])
            if not texts:
                self._json({"error": "empty texts"}, 400)
                return
            self._json({"embeddings": _encode(texts)})

        elif path == "/v1/embeddings":
            inp = payload.get("input", [])
            texts = inp if isinstance(inp, list) else [inp]
            if not texts:
                self._json({"error": "empty input"}, 400)
                return
            vecs = _encode(texts)
            self._json({
                "object": "list",
                "model": MODEL_NAME,
                "data": [{"object": "embedding", "index": i, "embedding": v} for i, v in enumerate(vecs)],
                "usage": {"prompt_tokens": 0, "total_tokens": 0},
            })
        else:
            self._json({"error": "not found"}, 404)


def main():
    global model
    logger.info(f"Loading {MODEL_NAME} ...")
    model = SentenceTransformer(MODEL_NAME)
    logger.info(f"Ready: dim={model.get_sentence_embedding_dimension()} on {HOST}:{PORT}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.daemon_threads = True
    server.serve_forever()


if __name__ == "__main__":
    main()
