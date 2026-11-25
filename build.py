#!/usr/bin/env python3
"""Build the GitHub Pages site from the page source.

site/index.html is written in Artifact format (no <!doctype>/<html>/<head>).
This wraps it into a complete standalone HTML document at docs/index.html,
which GitHub Pages serves. Run after every change to site/index.html:

    python3 build.py
"""
import os, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "site", "index.html")
OUT_DIR = os.path.join(ROOT, "docs")

BASE_CSS = (":root{color-scheme:light;box-sizing:border-box;"
            "padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
            "html{scroll-padding-top:env(safe-area-inset-top,0px)}"
            "body{margin:0;padding:0;font:14px -apple-system,BlinkMacSystemFont,sans-serif;background:#fff;color:#000}"
            "img{max-width:100%}[hidden]:not([hidden=until-found i]){display:none!important}")


def build():
    src = open(SRC, encoding="utf-8").read()
    if src.lstrip()[:15].lower().startswith("<!doctype"):
        html = src
    else:
        # Everything up to the end of the first <style> block belongs in <head>; the rest is the body.
        cut = src.index("</style>") + len("</style>")
        head, body = src[:cut], src[cut:]
        html = ("<!doctype html>\n<html lang=\"en-GB\">\n<head>\n<meta charset=\"utf-8\">\n"
                "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1,viewport-fit=cover\">\n"
                "<link rel=\"icon\" type=\"image/png\" href=\"favicon.png\">\n"
                f"<style>{BASE_CSS}</style>\n{head}\n</head>\n<body>\n{body.strip()}\n</body>\n</html>\n")
    os.makedirs(OUT_DIR, exist_ok=True)
    open(os.path.join(OUT_DIR, "index.html"), "w", encoding="utf-8").write(html)
    shutil.copyfile(os.path.join(ROOT, "Brand_assets", "breakin-emblem.png"), os.path.join(OUT_DIR, "favicon.png"))
    open(os.path.join(OUT_DIR, ".nojekyll"), "w").close()
    print(f"Built docs/index.html ({len(html):,} bytes)")


if __name__ == "__main__":
    build()
