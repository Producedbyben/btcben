#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import sys
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
SCRIPT_PATH = BASE_DIR / "miner_control.py"
CONFIG_PATH = BASE_DIR / "miner.conf"
LOG_PATH = BASE_DIR / "miner.log"
PID_PATH = BASE_DIR / "miner.pid"
HOST = os.environ.get("MINER_UI_HOST", "127.0.0.1")
PORT = int(os.environ.get("MINER_UI_PORT", "8080"))
LOCK = threading.Lock()

CONFIG_KEYS = [
    "MINER_BIN",
    "ALGO",
    "POOL_URL",
    "POOL_USER",
    "POOL_PASS",
    "USE_GPU",
    "USE_CPU",
    "THREADS",
    "GPU_INTENSITY",
    "POWER_PROFILE",
    "EXTRA_ARGS",
    "INTERNAL_DIFFICULTY",
]

HTML = """<!doctype html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>Bitcoin Lottery Miner Control Center</title>
<style>
:root{--bg:#0c1220;--card:#121a2b;--muted:#9db0d8;--ok:#22c55e;--warn:#f59e0b;--bad:#ef4444;--txt:#ecf2ff}
body{margin:0;background:linear-gradient(180deg,#0a0f1d,#0d1528);color:var(--txt);font-family:Inter,Arial,sans-serif}
.wrap{max-width:1120px;margin:24px auto;padding:0 16px}.grid{display:grid;grid-template-columns:1.2fr 1fr;gap:16px}
.card{background:var(--card);border:1px solid #223153;border-radius:14px;padding:16px;box-shadow:0 8px 25px rgba(0,0,0,.3)}
h1{margin:0 0 8px}h3{margin:4px 0 12px}.muted{color:var(--muted)}
.badge{display:inline-block;padding:6px 10px;border-radius:999px;background:#1e2a46;color:#bcd1ff;font-size:12px}
.row{display:flex;gap:8px;flex-wrap:wrap}.btn{border:0;border-radius:10px;padding:10px 14px;cursor:pointer;font-weight:600}
.start{background:var(--ok)}.stop{background:var(--bad);color:white}.refresh{background:#3b82f6;color:white}.save{background:#10b981}
label{font-size:12px;color:var(--muted)} input,select{width:100%;background:#0b1322;border:1px solid #2a3a62;color:#eaf1ff;border-radius:8px;padding:8px}
.two{display:grid;grid-template-columns:1fr 1fr;gap:10px}pre{max-height:320px;overflow:auto;background:#08101f;border-radius:8px;padding:10px;border:1px solid #1f2f4f}
.small{font-size:12px}.kpi{font-size:24px;font-weight:700}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
</style></head><body><div class='wrap'>
<h1>Bitcoin Lottery Miner Control Center</h1><div class='muted'>Noob-friendly controls for background mining, payout target, and power tuning.</div>
<div class='grid'>
<div class='card'><h3>Dashboard</h3>
<div class='row'><span class='badge' id='statusBadge'>Loading...</span><span class='badge' id='pidBadge'>PID: -</span><span class='badge' id='uptimeBadge'>Uptime: -</span></div>
<div class='two' style='margin-top:10px'><div><div class='small muted'>Estimated Hashrate (from logs)</div><div class='kpi' id='hashrate'>n/a</div></div><div><div class='small muted'>Last log update</div><div class='kpi' id='lastLog'>n/a</div></div></div>
<div class='row' style='margin-top:14px'><button class='btn start' onclick="act('start')">Start</button><button class='btn stop' onclick="act('stop')">Stop</button><button class='btn refresh' onclick='refreshAll()'>Refresh</button><button class='btn' onclick="act('doctor')">Doctor</button></div>
<h3>Live logs</h3><pre id='logs'>Loading logs...</pre></div>
<div class='card'><h3>Guided Configuration</h3><div class='two'>
<div><label>Miner Binary</label><input id='MINER_BIN'></div><div><label>Algorithm</label><input id='ALGO'></div>
<div><label>Pool URL</label><input id='POOL_URL'></div><div><label>Payout Wallet / Worker</label><input id='POOL_USER'></div>
<div><label>Pool Password</label><input id='POOL_PASS'></div><div><label>Power Profile</label><select id='POWER_PROFILE'><option>eco</option><option>balanced</option><option>performance</option></select></div>
<div><label>Use GPU</label><select id='USE_GPU'><option>true</option><option>false</option></select></div><div><label>Use CPU</label><select id='USE_CPU'><option>false</option><option>true</option></select></div>
<div><label>CPU Threads</label><input id='THREADS' type='number' min='1'></div><div><label>GPU Intensity</label><input id='GPU_INTENSITY'></div>
<div><label>Internal Difficulty</label><input id='INTERNAL_DIFFICULTY' type='number' min='1' max='250'></div><div></div>
</div><div style='margin-top:10px'><label>Extra Args</label><input id='EXTRA_ARGS'></div>
<div class='row' style='margin-top:12px'><button class='btn save' onclick='saveConfig()'>Save Config</button><button class='btn' onclick='loadConfig()'>Reload</button></div>
<div class='small muted' style='margin-top:8px'>Tip: For wallet-direct pools, set POOL_USER to your Bitcoin address so payouts go to your own wallet.</div>
</div></div></div>
<script>
async function api(path,opts={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opts});return await r.json();}
function setText(id,v){document.getElementById(id).textContent=v;}
async function loadConfig(){const d=await api('/api/config'); for(const [k,v] of Object.entries(d.config||{})){const el=document.getElementById(k); if(el) el.value=v;}}
async function saveConfig(){const payload={};['MINER_BIN','ALGO','POOL_URL','POOL_USER','POOL_PASS','USE_GPU','USE_CPU','THREADS','GPU_INTENSITY','POWER_PROFILE','EXTRA_ARGS','INTERNAL_DIFFICULTY'].forEach(k=>payload[k]=document.getElementById(k).value); const d=await api('/api/config',{method:'POST',body:JSON.stringify(payload)}); alert(d.message||'Saved'); refreshAll();}
async function refreshStatus(){const d=await api('/api/status'); setText('statusBadge', d.running?'Running':'Stopped'); setText('pidBadge', 'PID: '+(d.pid||'-')); setText('uptimeBadge','Uptime: '+(d.uptime||'-'));}
async function refreshLogs(){const d=await api('/api/logs'); setText('logs', d.logs||'(no logs yet)'); setText('hashrate',d.hashrate||'n/a'); setText('lastLog',d.last_update||'n/a');}
async function act(cmd){const d=await api('/api/'+cmd,{method:'POST'}); alert(d.output||d.error||cmd); refreshAll();}
async function refreshAll(){await Promise.all([refreshStatus(),refreshLogs(),loadConfig()]);}
refreshAll(); setInterval(refreshAll,5000);
</script></body></html>"""


def run_miner_command(command: str) -> tuple[int, str]:
    with LOCK:
        result = subprocess.run([sys.executable, str(SCRIPT_PATH), command], cwd=str(BASE_DIR), capture_output=True, text=True, check=False)
    return result.returncode, (result.stdout + result.stderr).strip()


def parse_config() -> dict[str, str]:
    cfg = {k: "" for k in CONFIG_KEYS}
    if not CONFIG_PATH.exists():
        return cfg
    for line in CONFIG_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"')
        if key in cfg:
            cfg[key] = value
    return cfg


def write_config(payload: dict[str, str]) -> None:
    base = parse_config()
    for key in CONFIG_KEYS:
        if key in payload:
            base[key] = str(payload[key]).strip()
    lines = [f"{k}={json.dumps(base[k]) if ' ' in base[k] else base[k]}" for k in CONFIG_KEYS]
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def get_runtime_status() -> dict[str, str | bool]:
    running = False
    pid = ""
    uptime = "-"
    if PID_PATH.exists():
        pid = PID_PATH.read_text(encoding="utf-8", errors="replace").strip()
        if pid.isdigit():
            proc = subprocess.run(["ps", "-p", pid, "-o", "etime="], capture_output=True, text=True, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                running = True
                uptime = proc.stdout.strip()
    return {"running": running, "pid": pid, "uptime": uptime}


def tail_logs() -> dict[str, str]:
    if not LOG_PATH.exists():
        return {"logs": "", "hashrate": "n/a", "last_update": "n/a"}
    content = LOG_PATH.read_text(encoding="utf-8", errors="replace").splitlines()
    lines = content[-180:]
    joined = "\n".join(lines)
    hashrate = "n/a"
    for line in reversed(lines):
        match = re.search(r"([0-9]+(?:\.[0-9]+)?\s*(?:[kMGT]?H/s))", line, re.I)
        if match:
            hashrate = match.group(1)
            break
    last_update = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(LOG_PATH.stat().st_mtime))
    return {"logs": joined, "hashrate": hashrate, "last_update": last_update}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args) -> None:
        return

    def _send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            data = HTML.encode("utf-8")
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        elif path == "/api/status":
            out = get_runtime_status()
            code, text = run_miner_command("status")
            out.update({"ok": code == 0, "output": text})
            self._send_json(HTTPStatus.OK, out)
        elif path == "/api/logs":
            self._send_json(HTTPStatus.OK, tail_logs())
        elif path == "/api/config":
            self._send_json(HTTPStatus.OK, {"config": parse_config()})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not Found"})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path in {"/api/start", "/api/stop", "/api/doctor"}:
            cmd = path.rsplit("/", 1)[-1]
            code, output = run_miner_command(cmd)
            self._send_json(HTTPStatus.OK if code == 0 else HTTPStatus.BAD_REQUEST, {"ok": code == 0, "output": output})
        elif path == "/api/config":
            payload = self._read_json()
            write_config(payload)
            self._send_json(HTTPStatus.OK, {"ok": True, "message": "Config saved."})
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not Found"})


def main() -> None:
    if not SCRIPT_PATH.exists():
        raise SystemExit(f"Missing control script: {SCRIPT_PATH}")
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Miner manager listening at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
