#!/usr/bin/env python3
"""Lightweight local web interface for managing start_miner.sh."""
from __future__ import annotations

import json
import os
import subprocess
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "start_miner.sh"
LOG_PATH = BASE_DIR / "miner.log"
HOST = os.environ.get("MINER_UI_HOST", "127.0.0.1")
PORT = int(os.environ.get("MINER_UI_PORT", "8080"))

LOCK = threading.Lock()

HTML = """<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width,initial-scale=1\" />
  <title>Bitcoin Miner Manager</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 2rem; background: #f6f7f9; color: #222; }
    .card { background: white; border-radius: 10px; padding: 1rem 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,.08); max-width: 900px; }
    button { margin-right: .5rem; margin-bottom: .75rem; padding: .6rem 1rem; border: 0; border-radius: 8px; cursor: pointer; }
    .start { background: #0f9d58; color: white; }
    .stop { background: #db4437; color: white; }
    .refresh { background: #4285f4; color: white; }
    pre { white-space: pre-wrap; background: #0b1020; color: #d6e1ff; padding: .75rem; border-radius: 8px; max-height: 350px; overflow: auto; }
    .status { font-weight: bold; margin: .5rem 0 1rem; }
    .muted { color: #666; font-size: .9rem; }
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Bitcoin Miner Manager</h1>
    <p class=\"muted\">Controls <code>miner/start_miner.sh</code> on this machine.</p>
    <div>
      <button class=\"start\" onclick=\"action('start')\">Start Miner</button>
      <button class=\"stop\" onclick=\"action('stop')\">Stop Miner</button>
      <button class=\"refresh\" onclick=\"refreshAll()\">Refresh</button>
    </div>
    <div class=\"status\" id=\"status\">Status: loading...</div>
    <h3>Recent Log Output</h3>
    <pre id=\"logs\">Loading logs...</pre>
  </div>
  <script>
    async function api(path, opts={}) {
      const res = await fetch(path, {headers: {'Content-Type': 'application/json'}, ...opts});
      return await res.json();
    }
    async function refreshStatus() {
      const data = await api('/api/status');
      document.getElementById('status').textContent = `Status: ${data.output.trim()}`;
    }
    async function refreshLogs() {
      const data = await api('/api/logs');
      document.getElementById('logs').textContent = data.logs || '(no logs yet)';
    }
    async function refreshAll() {
      await Promise.all([refreshStatus(), refreshLogs()]);
    }
    async function action(cmd) {
      const data = await api(`/api/${cmd}`, {method: 'POST'});
      alert(data.output.trim() || `${cmd} executed`);
      await refreshAll();
    }
    refreshAll();
    setInterval(refreshAll, 5000);
  </script>
</body>
</html>
"""


def run_miner_command(command: str) -> tuple[int, str]:
    with LOCK:
        result = subprocess.run(
            [str(SCRIPT_PATH), command],
            cwd=str(BASE_DIR),
            capture_output=True,
            text=True,
            check=False,
        )
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        data = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args) -> None:  # silence noisy access logs
        return

    def do_GET(self) -> None:  # noqa: N802 (BaseHTTPRequestHandler naming)
        path = urlparse(self.path).path
        if path == "/":
            self._send_html(HTML)
            return
        if path == "/api/status":
            code, output = run_miner_command("status")
            self._send_json(HTTPStatus.OK, {"ok": code == 0, "output": output})
            return
        if path == "/api/logs":
            if LOG_PATH.exists():
                logs = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]
                self._send_json(HTTPStatus.OK, {"logs": "\n".join(logs)})
            else:
                self._send_json(HTTPStatus.OK, {"logs": ""})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not Found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in {"/api/start", "/api/stop"}:
            cmd = path.rsplit("/", 1)[-1]
            code, output = run_miner_command(cmd)
            status = HTTPStatus.OK if code == 0 else HTTPStatus.BAD_REQUEST
            self._send_json(status, {"ok": code == 0, "output": output})
            return
        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not Found"})


def main() -> None:
    if not SCRIPT_PATH.exists():
        raise SystemExit(f"Missing control script: {SCRIPT_PATH}")

    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Miner manager listening at http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
