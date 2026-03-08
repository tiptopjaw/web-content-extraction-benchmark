#!/usr/bin/env python3
"""Annotation review server for web content extraction benchmark."""
import http.server
import json
import random
from pathlib import Path
from datetime import datetime

PORT = 8777
BASE_DIR = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = BASE_DIR / "benchmark"
HTML_DIR = BENCHMARK_DIR / "html"
GT_DIR = BENCHMARK_DIR / "ground-truth"
TOOL_DIR = Path(__file__).resolve().parent
VERIFIED_DIR = TOOL_DIR / "verified"
PROGRESS_FILE = TOOL_DIR / "progress.json"
FILE_LIST_FILE = TOOL_DIR / "file_list.json"
TARGET_COUNT = 500

_file_list = None
_files_meta = None


def get_file_list():
    global _file_list
    if _file_list is not None:
        return _file_list

    if FILE_LIST_FILE.exists():
        with open(FILE_LIST_FILE) as f:
            _file_list = json.load(f)
        return _file_list

    gt_files = {p.stem for p in GT_DIR.glob("*.json")}
    html_files = {p.stem for p in HTML_DIR.glob("*.html")}
    valid = sorted(gt_files & html_files)

    random.seed(42)
    selected = random.sample(valid, min(TARGET_COUNT, len(valid)))
    selected.sort()

    with open(FILE_LIST_FILE, "w") as f:
        json.dump(selected, f, indent=2)

    _file_list = selected
    return _file_list


def get_files_meta():
    """Build file metadata list (cached)."""
    global _files_meta
    if _files_meta is not None:
        return _files_meta

    progress = get_progress()
    result = []
    for fid in get_file_list():
        gt_path = GT_DIR / f"{fid}.json"
        url = ""
        page_type = ""
        if gt_path.exists():
            with open(gt_path, encoding="utf-8") as f:
                gt = json.load(f)
            url = gt.get("url", "")
            page_type = (
                gt.get("_internal", {})
                .get("page_type", {})
                .get("primary", "")
            )
        status = progress.get(fid, {}).get("status", "pending")
        result.append(
            {"id": fid, "status": status, "url": url, "page_type": page_type}
        )
    _files_meta = result
    return _files_meta


def invalidate_meta_cache():
    global _files_meta
    _files_meta = None


def get_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {}


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def progress_summary():
    progress = get_progress()
    fl = get_file_list()
    counts = {"pending": 0, "approved": 0, "flagged": 0, "skipped": 0}
    for fid in fl:
        s = progress.get(fid, {}).get("status", "pending")
        counts[s] = counts.get(s, 0) + 1
    counts["total"] = len(fl)
    return counts


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]

        if path == "/":
            self._serve_file(TOOL_DIR / "index.html", "text/html")
        elif path == "/api/files":
            self._json(get_files_meta())
        elif path == "/api/progress":
            self._json(progress_summary())
        elif path.startswith("/api/file/"):
            parts = path.split("/")
            if len(parts) >= 5:
                fid = parts[3]
                endpoint = parts[4]
                if endpoint == "html":
                    self._serve_file(HTML_DIR / f"{fid}.html", "text/html")
                elif endpoint == "gt":
                    self._serve_gt(fid)
                elif endpoint == "verified":
                    self._serve_verified(fid)
                else:
                    self.send_error(404)
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def do_POST(self):
        path = self.path.split("?")[0]

        if path.startswith("/api/file/") and path.endswith("/verify"):
            fid = path.split("/")[3]
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            data = json.loads(body)
            self._save_verification(fid, data)
            self._json({"ok": True})
        elif path.startswith("/api/file/") and path.endswith("/remove"):
            fid = path.split("/")[3]
            self._remove_file(fid)
            self._json({"ok": True, "remaining": len(get_file_list())})
        else:
            self.send_error(404)

    def _serve_gt(self, fid):
        p = GT_DIR / f"{fid}.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                self._json(json.load(f))
        else:
            self.send_error(404)

    def _serve_verified(self, fid):
        p = VERIFIED_DIR / f"{fid}.json"
        if p.exists():
            with open(p, encoding="utf-8") as f:
                self._json(json.load(f))
        else:
            self.send_error(404)

    def _remove_file(self, fid):
        global _file_list
        fl = get_file_list()
        if fid in fl:
            fl.remove(fid)
            with open(FILE_LIST_FILE, "w") as f:
                json.dump(fl, f, indent=2)
            _file_list = fl
        # Clean from progress too
        progress = get_progress()
        progress.pop(fid, None)
        save_progress(progress)
        # Remove verified file if exists
        vpath = VERIFIED_DIR / f"{fid}.json"
        if vpath.exists():
            vpath.unlink()
        invalidate_meta_cache()

    def _save_verification(self, fid, data):
        data["verified_at"] = datetime.now().isoformat()
        vpath = VERIFIED_DIR / f"{fid}.json"
        with open(vpath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        progress = get_progress()
        progress[fid] = {
            "status": data.get("status", "approved"),
            "verified_at": data["verified_at"],
        }
        save_progress(progress)
        invalidate_meta_cache()

    def _serve_file(self, filepath, content_type):
        filepath = Path(filepath)
        if not filepath.exists():
            self.send_error(404)
            return
        content = filepath.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", len(content))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", len(body))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # quiet


def main():
    VERIFIED_DIR.mkdir(parents=True, exist_ok=True)
    fl = get_file_list()
    ps = progress_summary()

    print(f"Benchmark Annotation Tool")
    print(f"  Files: {len(fl)}")
    print(
        f"  Progress: {ps['approved']} approved, {ps['flagged']} flagged, "
        f"{ps['skipped']} skipped, {ps['pending']} pending"
    )
    print(f"  http://localhost:{PORT}")

    server = http.server.HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
        server.shutdown()


if __name__ == "__main__":
    main()
