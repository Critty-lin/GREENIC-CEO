#!/usr/bin/env python3
import json
import math
import os
import posixpath
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "runs.json"
PORT = int(os.environ.get("PORT") or 8000)
ALLOW_ORIGIN = os.environ.get("ALLOW_ORIGIN", "*")
LOCK = threading.Lock()


def load_rows():
    if not DATA.exists():
        return []
    try:
        data = json.loads(DATA.read_text(encoding="utf-8") or "[]")
        return data if isinstance(data, list) else []
    except Exception:
        return []


def save_rows(rows):
    DATA.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA.with_suffix(".tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    tmp.replace(DATA)


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def handle_error(self, request, client_address):
        exc = sys.exc_info()[1]
        if isinstance(exc, (BrokenPipeError, ConnectionResetError)):
            return
        super().handle_error(request, client_address)


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _blocked(self, path):
        path = (path or "/").split("?", 1)[0].split("#", 1)[0]
        norm = "/" + posixpath.normpath(unquote(path)).lstrip("/")
        parts = [p for p in norm.split("/") if p]
        if parts and (parts[0].lower() == "data" or any(p.startswith(".") for p in parts)):
            return True
        return norm.lower().endswith((".py", ".pyc", ".toml", ".log"))

    def end_headers(self):
        if ALLOW_ORIGIN:
            self.send_header("Access-Control-Allow-Origin", ALLOW_ORIGIN)
            self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_OPTIONS(self):
        if urlparse(self.path).path in ("/api/runs", "/api/honor"):
            self.send_response(204)
            self.end_headers()
            return
        self.send_error(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if self._blocked(self.path):
            self.send_error(404)
            return
        if path == "/api/runs":
            self._json(load_rows())
            return
        if path == "/api/honor":
            q = parse_qs(parsed.query)
            try:
                score = int((q.get("score") or ["0"])[0])
            except Exception:
                score = 0
            best = {}
            for r in load_rows():
                d = str(r.get("device") or "unknown")[:40]
                s = int(r.get("score") or 0)
                if d not in best or s > best[d]:
                    best[d] = s
            total = len(best)
            if total <= 1:
                self._json({"total": total, "beat": 0, "pct": 100, "first": True})
                return
            worse = sum(1 for s in best.values() if s < score)
            pct = int(round(100.0 * worse / total))
            self._json({"total": total, "beat": worse, "pct": max(0, min(100, pct)), "first": False})
            return
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/runs":
            self.send_error(404)
            return
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except (TypeError, ValueError):
            n = 0
        raw = self.rfile.read(max(0, min(n, 8192)))
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self.send_error(400)
            return

        def num(key, default=0):
            try:
                return int(body.get(key) if body.get(key) is not None else default)
            except Exception:
                return default

        def flt(key, default=0.0):
            try:
                v = float(body.get(key) if body.get(key) is not None else default)
                return v if math.isfinite(v) else default
            except Exception:
                return default

        row = {
            "score": num("score"),
            "ending": str(body.get("ending") or "")[:40],
            "endingId": str(body.get("endingId") or "")[:24],
            "trust": max(0, min(100, num("trust"))),
            "stock": round(flt("stock"), 2),
            "rivals": num("rivals"),
            "beaten": num("beaten"),
            "quote": str(body.get("quote") or "")[:24],
            "device": str(body.get("device") or "unknown")[:40],
            "at": int(time.time()),
        }
        with LOCK:
            rows = load_rows()
            rows.append(row)
            if len(rows) > 2000:
                rows = rows[-2000:]
            save_rows(rows)
            total = len(rows)
        self._json({"ok": True, "id": total})

    def _json(self, obj):
        blob = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if not DATA.exists():
        DATA.write_text("[]", encoding="utf-8")
    Server(("0.0.0.0", PORT), Handler).serve_forever()
