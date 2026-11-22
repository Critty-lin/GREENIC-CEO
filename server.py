#!/usr/bin/env python3
import json
import os
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "board.json"
PORT = int(os.environ["PORT"])


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


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path == "/api/board":
            rows = sorted(load_rows(), key=lambda r: -int(r.get("score") or 0))[:20]
            self._json(rows)
            return
        return super().do_GET()

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        if path != "/api/board":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(max(0, min(n, 4096)))
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self.send_error(400)
            return
        name = str(body.get("name") or "").strip()[:12] or "匿名神人"
        name = name.replace("<", "").replace(">", "")
        try:
            score = int(body.get("score") or 0)
        except Exception:
            score = 0
        ending = str(body.get("ending") or "")[:40]
        rows = load_rows()
        rows.append({"name": name, "score": score, "ending": ending, "at": int(time.time())})
        rows = sorted(rows, key=lambda r: -int(r.get("score") or 0))[:50]
        save_rows(rows)
        rank = next((i + 1 for i, r in enumerate(rows) if r["name"] == name and r["score"] == score), 0)
        self._json({"ok": True, "rank": rank})

    def _json(self, obj):
        blob = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(blob)))
        self.end_headers()
        self.wfile.write(blob)

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    DATA.parent.mkdir(parents=True, exist_ok=True)
    if not DATA.exists():
        DATA.write_text("[]", encoding="utf-8")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
