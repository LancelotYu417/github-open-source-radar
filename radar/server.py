"""Zero-dependency local HTTP UI and JSON API."""
import json
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from .store import connect, ranking

ROOT = Path(__file__).resolve().parent.parent

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlsplit(self.path)
        if parsed.path == "/api/rankings":
            qs = parse_qs(parsed.query)
            window = qs.get("window", ["30d"])[0]
            language = qs.get("language", [""])[0]
            try:
                db = connect()
                rows = ranking(db, window=window, language=language)
                total = db.execute("SELECT COUNT(*) FROM repos").fetchone()[0]
                run = db.execute("SELECT * FROM sync_runs ORDER BY id DESC LIMIT 1").fetchone()
                db.close()
                self.send_json({"window":window,"candidate_pool":total,
                                "coverage":"sampled_candidates_not_global",
                                "last_sync":dict(run) if run else None,"items":rows})
            except ValueError as error:
                self.send_json({"error":str(error)},400)
        elif parsed.path in ("/", "/index.html"):
            data = (ROOT / "static" / "index.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_json({"error":"Not found"},404)

    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

def main():
    print("GitHub Open Source Radar at http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1",8765),Handler).serve_forever()

if __name__ == "__main__":
    main()
