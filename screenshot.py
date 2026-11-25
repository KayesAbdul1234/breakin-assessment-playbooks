#!/usr/bin/env python3
"""Full-page screenshots of a localhost page via headless Chrome + DevTools protocol.
macOS stand-in for `node screenshot.mjs` (no Node/Puppeteer needed; standard library only).

  python3 screenshot.py <url> [label] [--mobile] [--dark] [--width N] [--top N] [--from Y] [--eval JS]

  --mobile   390px wide, touch/mobile emulation (true phone width, unlike --window-size)
  --dark     prefers-color-scheme: dark (default is light)
  --top N    capture only the first N CSS px (close-up of the top of the page)
  --from Y   start the capture at Y CSS px (use with --top for a slice)
  --eval JS  run JavaScript in the page before capturing (awaited if it returns a promise),
             e.g. to click through an interaction and screenshot the resulting state

Saves to "./temporary screenshots/screenshot-N[-label].png" (auto-incremented, never overwritten)
and reports page height and any horizontal overflow (elements wider than the viewport).
"""
import base64, json, os, random, socket, struct, subprocess, sys, tempfile, time, urllib.request, shutil, glob

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "temporary screenshots")


class WS:
    """Minimal websocket client (enough for CDP)."""
    def __init__(self, url):
        assert url.startswith("ws://")
        hostport, path = url[5:].split("/", 1)
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)), timeout=300)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
                        f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        buf = b""
        while b"\r\n\r\n" not in buf:
            buf += self.s.recv(4096)
        if b" 101 " not in buf.split(b"\r\n")[0]:
            raise RuntimeError("websocket handshake failed: " + buf[:200].decode(errors="replace"))
        self.rest = buf.split(b"\r\n\r\n", 1)[1]
        self.next_id = 0
        self.events = []

    def _read(self, n):
        while len(self.rest) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise ConnectionError("socket closed")
            self.rest += chunk
        out, self.rest = self.rest[:n], self.rest[n:]
        return out

    def send(self, text):
        data = text.encode()
        hdr = bytes([0x81])
        n = len(data)
        if n < 126: hdr += bytes([0x80 | n])
        elif n < 65536: hdr += bytes([0x80 | 126]) + struct.pack(">H", n)
        else: hdr += bytes([0x80 | 127]) + struct.pack(">Q", n)
        mask = os.urandom(4)
        self.s.sendall(hdr + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b""
        while True:
            b1, b2 = self._read(2)
            n = b2 & 0x7F
            if n == 126: n = struct.unpack(">H", self._read(2))[0]
            elif n == 127: n = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(n)
            op = b1 & 0x0F
            if op == 0x9:  # ping
                continue
            msg += payload
            if b1 & 0x80:
                return json.loads(msg)

    def call(self, method, **params):
        self.next_id += 1
        my = self.next_id
        self.send(json.dumps({"id": my, "method": method, "params": params}))
        while True:
            m = self.recv()
            if "method" in m:
                self.events.append(m)
            if m.get("id") == my:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})


def main():
    args = sys.argv[1:]
    if not args or args[0].startswith("-"):
        print(__doc__); sys.exit(1)
    url = args.pop(0)
    if url.startswith("file://"):
        sys.exit("Refusing file:// URL. Start the server (python3 serve.py) and use http://localhost:3000")
    label, width, mobile, dark, top, y0, js = "", 1440, False, False, None, 0, None
    while args:
        a = args.pop(0)
        if a == "--mobile": width, mobile = 390, True
        elif a == "--dark": dark = True
        elif a == "--width": width = int(args.pop(0))
        elif a == "--top": top = int(args.pop(0))
        elif a == "--from": y0 = int(args.pop(0))
        elif a == "--eval": js = args.pop(0)
        else: label = a

    os.makedirs(OUT, exist_ok=True)
    n = 1
    while os.path.exists(f"{OUT}/screenshot-{n}.png") or glob.glob(f"{OUT}/screenshot-{n}-*.png"):
        n += 1
    path = f"{OUT}/screenshot-{n}{'-' + label if label else ''}.png"

    port = random.randint(9300, 9800)
    profile = tempfile.mkdtemp()
    proc = subprocess.Popen([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                             "--no-default-browser-check", f"--user-data-dir={profile}",
                             f"--remote-debugging-port={port}", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        targets = None
        for _ in range(100):
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json/list", timeout=1))
                if any(t["type"] == "page" for t in targets): break
            except Exception:
                pass
            time.sleep(0.1)
        page = next(t for t in targets if t["type"] == "page")
        ws = WS(page["webSocketDebuggerUrl"])
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        ws.call("Log.enable")
        ws.call("Emulation.setDeviceMetricsOverride", width=width, height=900 if not mobile else 844,
                deviceScaleFactor=2 if mobile else 1, mobile=mobile)
        if mobile:
            ws.call("Emulation.setTouchEmulationEnabled", enabled=True)
        ws.call("Emulation.setEmulatedMedia", features=[{"name": "prefers-color-scheme", "value": "dark" if dark else "light"}])
        ws.call("Page.navigate", url=url)
        deadline = time.time() + 20
        while time.time() < deadline:
            m = ws.recv()
            if "method" in m: ws.events.append(m)
            if m.get("method") == "Page.loadEventFired": break
        ws.call("Runtime.evaluate", expression="document.fonts.ready.then(()=>1)", awaitPromise=True)
        time.sleep(1.2)  # let entrance animations settle
        if js:
            r = ws.call("Runtime.evaluate", expression=js, awaitPromise=True, returnByValue=True)
            if r.get("exceptionDetails"):
                print("eval error:", r["exceptionDetails"].get("exception", {}).get("description", r["exceptionDetails"]))
            elif r.get("result", {}).get("value") is not None:
                print("eval result:", r["result"]["value"])
            time.sleep(0.6)
        info = ws.call("Runtime.evaluate", returnByValue=True, expression="""(()=>{
            const W=innerWidth, de=document.documentElement;
            const wide=[...document.querySelectorAll('body *')].filter(e=>{const r=e.getBoundingClientRect();
              return r.width>0 && (r.right>W+1) && getComputedStyle(e).position!=='fixed';})
              .filter(e=>!e.closest('[style*=overflow],.peek')).slice(0,8)
              .map(e=>e.tagName.toLowerCase()+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\\s+/).join('.'):'')+' right='+Math.round(e.getBoundingClientRect().right));
            return {w:W, scrollW:de.scrollWidth, h:Math.ceil(de.scrollHeight), wide};})()""")["result"]["value"]
        h = (info["h"] - y0) if top is None else min(top, info["h"] - y0)
        shot = ws.call("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                       clip={"x": 0, "y": y0, "width": width, "height": h, "scale": 1})
        with open(path, "wb") as f:
            f.write(base64.b64decode(shot["data"]))
        print(path)
        print(f"viewport {info['w']}px · page height {info['h']}px · scrollWidth {info['scrollW']}px"
              + ("  ⚠ HORIZONTAL OVERFLOW" if info["scrollW"] > info["w"] else "  · no horizontal overflow"))
        for w in info["wide"]:
            print("  wider than viewport:", w)
        errs = []
        for ev in ws.events:
            m, prm = ev.get("method"), ev.get("params", {})
            if m == "Runtime.exceptionThrown":
                d = prm.get("exceptionDetails", {})
                errs.append("exception: " + (d.get("exception", {}).get("description") or d.get("text", "")).split("\n")[0])
            elif m == "Runtime.consoleAPICalled" and prm.get("type") in ("error", "assert"):
                errs.append("console.error: " + " ".join(str(a.get("value", a.get("description", ""))) for a in prm.get("args", [])))
            elif m == "Log.entryAdded" and prm.get("entry", {}).get("level") == "error":
                u = prm["entry"].get("url", "")
                if not u.endswith("/favicon.ico"):
                    errs.append("log: " + prm["entry"].get("text", "") + (" " + u if u else ""))
        print(f"⚠ {len(errs)} JS/console error(s)" if errs else "· no JS or console errors")
        for e in errs[:10]:
            print("  " + e)
    finally:
        proc.terminate()
        try: proc.wait(5)
        except Exception: proc.kill()
        shutil.rmtree(profile, ignore_errors=True)


if __name__ == "__main__":
    main()
