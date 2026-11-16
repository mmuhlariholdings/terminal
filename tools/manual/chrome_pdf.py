#!/usr/bin/env python3
"""Print a page to PDF with headless Chrome, waiting until the page says it is ready (document.title == ready_title).

Uses Chrome's DevTools protocol over a minimal standard-library WebSocket client, so nothing needs installing.
Chrome's own --print-to-pdf can't wait for a long Paged.js layout, which is why this exists.
"""
import base64
import json
import os
import random
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request


class WS:
    """Just enough WebSocket (RFC 6455) for the DevTools protocol: text frames, client masking, large messages."""

    def __init__(self, url):
        assert url.startswith("ws://")
        hostport, path = url[5:].split("/", 1)
        host, port = hostport.split(":")
        self.s = socket.create_connection((host, int(port)))
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall((f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n").encode())
        resp = b""
        while b"\r\n\r\n" not in resp:
            resp += self.s.recv(4096)
        if b" 101 " not in resp.split(b"\r\n")[0]:
            raise RuntimeError("WebSocket handshake failed: " + resp[:200].decode(errors="replace"))
        self.buf = resp.split(b"\r\n\r\n", 1)[1]
        self.n = 0

    def _read(self, n):
        while len(self.buf) < n:
            chunk = self.s.recv(1 << 20)
            if not chunk:
                raise RuntimeError("connection closed")
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def send(self, obj):
        data = json.dumps(obj).encode()
        head = bytearray([0x81])
        ln = len(data)
        if ln < 126:
            head.append(0x80 | ln)
        elif ln < 65536:
            head.append(0x80 | 126); head += struct.pack(">H", ln)
        else:
            head.append(0x80 | 127); head += struct.pack(">Q", ln)
        mask = os.urandom(4)
        self.s.sendall(bytes(head) + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def recv(self):
        msg = b""
        while True:
            b0, b1 = self._read(2)
            ln = b1 & 0x7F
            if ln == 126:
                ln = struct.unpack(">H", self._read(2))[0]
            elif ln == 127:
                ln = struct.unpack(">Q", self._read(8))[0]
            payload = self._read(ln)
            op = b0 & 0x0F
            if op == 0x9:          # ping: ignore
                continue
            msg += payload
            if b0 & 0x80:
                return json.loads(msg.decode())

    def call(self, method, **params):
        self.n += 1
        my = self.n
        self.send({"id": my, "method": method, "params": params})
        while True:
            m = self.recv()
            if m.get("id") == my:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})


def print_pdf(chrome, url, out_pdf, ready_title="paged", timeout=900, log=print):
    port = random.randint(20000, 40000)
    prof = tempfile.mkdtemp(prefix="wlpdf")
    proc = subprocess.Popen([chrome, "--headless=new", f"--user-data-dir={prof}", f"--remote-debugging-port={port}",
                             "--allow-file-access-from-files", "--no-first-run", "about:blank"],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while True:
            try:
                targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=2))
                page = next(t for t in targets if t.get("type") == "page")
                break
            except Exception:
                if time.time() - t0 > 30:
                    raise RuntimeError("Chrome did not start")
                time.sleep(0.3)
        ws = WS(page["webSocketDebuggerUrl"])
        ws.call("Page.enable")
        ws.call("Runtime.enable")
        ws.call("Page.navigate", url=url)
        t0 = time.time()
        last = ""
        while True:
            title = ws.call("Runtime.evaluate", expression="document.title + '|' + document.querySelectorAll('.pagedjs_page').length",
                            returnByValue=True)["result"].get("value", "")
            if title != last:
                log(f"  layout: {title}  ({time.time() - t0:.0f} s)")
                last = title
            if title.split("|")[0] == ready_title:
                break
            if time.time() - t0 > timeout:
                raise RuntimeError(f"page not ready after {timeout} s (title {title!r})")
            time.sleep(1)
        res = ws.call("Page.printToPDF", printBackground=True, preferCSSPageSize=True, displayHeaderFooter=False,
                      marginTop=0, marginBottom=0, marginLeft=0, marginRight=0, generateDocumentOutline=True)
        with open(out_pdf, "wb") as fh:
            fh.write(base64.b64decode(res["data"]))
    finally:
        proc.terminate()
        try:
            proc.wait(10)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(prof, ignore_errors=True)
