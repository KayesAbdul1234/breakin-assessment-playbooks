#!/usr/bin/env python3
"""Local dev server for the BreakIn site (macOS stand-in for `node serve.mjs`).

Serves the project root at http://localhost:3000.
HTML files written in Artifact format (no <!doctype>) are wrapped in the same
minimal skeleton the Artifact host adds at publish time, so local screenshots
render the way the published page does (standards mode, safe-area padding).

Usage:  python3 serve.py            (run from the project root)
"""
import http.server, os, socketserver

PORT = 3000
ROOT = os.path.dirname(os.path.abspath(__file__))

SKELETON_HEAD = (
    '<!doctype html><html><head><meta charset=utf8>'
    '<meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover">'
    '<style>:root{color-scheme:light;box-sizing:border-box;'
    'padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}'
    'html{scroll-padding-top:env(safe-area-inset-top,0px)}'
    'body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}'
    'img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}</style>'
    '</head><body>\n'
)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            idx = os.path.join(path, "index.html")
            if os.path.exists(idx) and self.path.endswith("/"):
                path = idx
        if path.endswith(".html") and os.path.isfile(path):
            with open(path, "rb") as f:
                body = f.read()
            if not body.lstrip()[:15].lower().startswith(b"<!doctype"):
                body = SKELETON_HEAD.encode() + body + b"\n</body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            from io import BytesIO
            return BytesIO(body)
        return super().send_head()

    def log_message(self, *a):
        pass


class Server(socketserver.ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True


if __name__ == "__main__":
    with Server(("127.0.0.1", PORT), Handler) as s:
        print(f"Serving {ROOT} at http://localhost:{PORT}")
        s.serve_forever()
