"""admin_server.py — local-only HTTP wrapper around series_admin.py.

plans/reliable-series-powertrain.md Step 5A/5B. Stdlib http.server only (no
new dependency). Binds to 127.0.0.1 exclusively — never 0.0.0.0 — and is
never imported by any export/build script, so it cannot end up in the
public static build.

  GET     /queue   -> JSON list from series_admin.list_unresolved()
  POST    /review  -> JSON body -> series_admin.save_review()
  OPTIONS *        -> CORS preflight for the two routes above

CORS is scoped to the Next.js local dev origins only (never a wildcard) so
the index page (running under `next dev`) can call this service directly.
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from series_admin import ReviewValidationError, list_unresolved, save_review

HOST = "127.0.0.1"
ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000"}


class Handler(BaseHTTPRequestHandler):
    def _cors_headers(self):
        origin = self.headers.get("Origin")
        if origin in ALLOWED_ORIGINS:
            self.send_header("Access-Control-Allow-Origin", origin)
            self.send_header("Vary", "Origin")

    def _send_json(self, status, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors_headers()
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "600")
        self.end_headers()

    def do_GET(self):
        if self.path == "/queue":
            self._send_json(200, list_unresolved())
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/review":
            self._send_json(404, {"error": "not found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
            row = save_review(payload)
            self._send_json(200, row)
        except ReviewValidationError as e:
            self._send_json(400, {"errors": e.issues})
        except (ValueError, json.JSONDecodeError) as e:
            self._send_json(400, {"errors": [str(e)]})

    def log_message(self, format, *args):
        pass  # ponytail: stdlib default logs every request to stderr; stay quiet


def main():
    port = int(os.environ.get("SERIES_ADMIN_PORT", "8765"))
    server = ThreadingHTTPServer((HOST, port), Handler)
    print(f"series admin review server on http://{HOST}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
