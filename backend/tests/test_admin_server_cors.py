"""Tests for admin_server.py CORS scoping (plans/reliable-series-powertrain.md Step 5B).

No pytest — matches the existing test_*.py convention. Starts the real
ThreadingHTTPServer on an ephemeral 127.0.0.1 port against a temp registry,
exercises it with urllib, then shuts it down. Exits 0 on PASS, 1 on FAIL.
"""
import csv
import os
import sys
import tempfile
import threading
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from admin_server import Handler
from series_registry import COLUMNS

failures = []


def run_tests():
    with tempfile.TemporaryDirectory() as tmp:
        registry_path = Path(tmp) / "series_registry.csv"
        with open(registry_path, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNS)
        os.environ["SERIES_REGISTRY_PATH"] = str(registry_path)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        port = server.server_address[1]
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{port}"

        try:
            # 1. Allowed dev origin gets reflected, never a wildcard
            req = urllib.request.Request(f"{base}/queue", headers={"Origin": "http://localhost:3000"})
            with urllib.request.urlopen(req) as resp:
                allow = resp.headers.get("Access-Control-Allow-Origin")
                if allow != "http://localhost:3000":
                    failures.append(f"Allowed origin reflected: got {allow!r}")

            # 2. Unknown origin gets no CORS header (browser will block it)
            req = urllib.request.Request(f"{base}/queue", headers={"Origin": "http://evil.example"})
            with urllib.request.urlopen(req) as resp:
                allow = resp.headers.get("Access-Control-Allow-Origin")
                if allow is not None:
                    failures.append(f"Unknown origin gets no CORS header: got {allow!r}")

            # 3. OPTIONS preflight for POST succeeds with the right allow-list
            req = urllib.request.Request(
                f"{base}/review", method="OPTIONS",
                headers={"Origin": "http://127.0.0.1:3000", "Access-Control-Request-Method": "POST"},
            )
            with urllib.request.urlopen(req) as resp:
                if resp.status != 204:
                    failures.append(f"OPTIONS preflight succeeds: got status {resp.status}")
                methods = resp.headers.get("Access-Control-Allow-Methods", "")
                if "POST" not in methods:
                    failures.append(f"OPTIONS preflight allows POST: got {methods!r}")
                if resp.headers.get("Access-Control-Allow-Origin") != "http://127.0.0.1:3000":
                    failures.append("OPTIONS preflight reflects allowed origin")

            # 4. No wildcard anywhere in the source
            src = (BACKEND / "admin_server.py").read_text(encoding="utf-8")
            if '"*"' in src or "'*'" in src:
                failures.append("No wildcard origin: admin_server.py contains a literal '*'")
        finally:
            server.shutdown()
            server.server_close()
            del os.environ["SERIES_REGISTRY_PATH"]


if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in admin_server CORS tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All admin_server CORS tests passed successfully.")
