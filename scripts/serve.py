#!/usr/bin/env python3
"""Development server that proxies /api/ requests to tempestd.

Usage:
    python3 scripts/serve.py                                          # tempestd at localhost:8080
    python3 scripts/serve.py --backend https://tempestd.example.com   # remote tempestd
    python3 scripts/serve.py --port 9000                              # different dashboard port
"""

import argparse
import http.server
import os
import urllib.request
import urllib.error
import ssl

# Serve files from the repo root (one level up from this script)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    backend = "http://localhost:8080"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT_DIR, **kwargs)

    def do_GET(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def do_OPTIONS(self):
        if self.path.startswith("/api/"):
            self._proxy()
        else:
            super().do_GET()

    def _proxy(self):
        url = self.backend.rstrip("/") + self.path
        try:
            req = urllib.request.Request(url, method=self.command)
            for key, val in self.headers.items():
                if key.lower() not in ("host", "connection"):
                    req.add_header(key, val)
            ctx = ssl.create_default_context()
            resp = urllib.request.urlopen(req, context=ctx, timeout=30)
            self.send_response(resp.status)
            for key, val in resp.getheaders():
                if key.lower() not in ("transfer-encoding", "connection"):
                    self.send_header(key, val)
            self.end_headers()
            self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error": "{e}"}}'.encode())

    def log_message(self, format, *args):
        status = args[1] if len(args) > 1 else ""
        print(f"  {self.command} {self.path} {status}")


def main():
    parser = argparse.ArgumentParser(description="Dashboard dev server with API proxy")
    parser.add_argument("--port", type=int, default=8000, help="Port to serve on (default: 8000)")
    parser.add_argument("--backend", default="http://localhost:8080", help="tempestd backend URL")
    args = parser.parse_args()

    ProxyHandler.backend = args.backend
    server = http.server.HTTPServer(("", args.port), ProxyHandler)
    print(f"Dashboard: http://localhost:{args.port}")
    print(f"Backend:   {args.backend}")
    print(f"Serving:   {ROOT_DIR}")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
