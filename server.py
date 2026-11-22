#!/usr/bin/env python3
import json
import os
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "runs.json"
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
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/api/runs":
            self._json(load_rows())
            return
        if path == "/api/honor":
            q = parse_qs(parsed.query)
            try:
                score = int((q.get("score") or ["0"])[0])
            except Exception:
                score = 0
            rows = load_rows()
            total = len(rows)
            if total <= 1:
                self._json({"total": total, "beat": 0, "pct": 100, "first": True})
                return
            others = total - 1
            worse = sum(1 for r in rows if int(r.get("score") or 0) < score)
            # 不含自己时：比自己低的局 / 其他局
            if others > 0:
                # 当前这局已写入，则 worse 含「严格低于自己」的全部，自己那条不算 worse
                pct = int(round(100.0 * worse / others))
            else:
                pct = 100
            self._json({"total": total, "beat": worse, "pct": max(0, min(100, pct)), "first": False})
            return
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/runs":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length") or 0)
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
                return float(body.get(key) if body.get(key) is not None else default)
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
            "at": int(time.time()),
        }
        rows = load_rows()
        rows.append(row)
        if len(rows) > 2000:
            rows = rows[-2000:]
        save_rows(rows)
        self._json({"ok": True, "id": len(rows)})

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
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
