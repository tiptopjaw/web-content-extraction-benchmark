#!/usr/bin/env python3
"""Tiny HTTP server that receives HTML via POST and saves to benchmark/html/"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

HTML_DIR = Path(__file__).parent.parent / "benchmark" / "html"
HTML_DIR.mkdir(parents=True, exist_ok=True)

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        data = json.loads(body)
        file_id = data["id"]
        html = data["html"]
        path = HTML_DIR / f"{file_id}.html"
        path.write_text(html, encoding="utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"ok": True, "size": len(html), "path": str(path)}).encode())
        print(f"  Saved {file_id}.html ({len(html)//1024} KB)")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, format, *args):
        pass  # suppress default logging

print(f"HTML receiver listening on http://localhost:9876")
print(f"Saving to {HTML_DIR}")
HTTPServer(("127.0.0.1", 9876), Handler).serve_forever()
