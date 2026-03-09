#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shlex
import shutil
import signal
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "miner.conf"
PID_PATH = BASE_DIR / "miner.pid"
LOG_PATH = BASE_DIR / "miner.log"


def parse_config() -> dict[str, str]:
    if not CONFIG_PATH.exists():
        raise RuntimeError(f"Missing {CONFIG_PATH}. Open the app and click Save Config first.")

    data: dict[str, str] = {}
    for raw in CONFIG_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"')

    required = ["MINER_BIN", "POOL_URL", "POOL_USER", "POOL_PASS"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        raise RuntimeError(f"Missing required config keys: {', '.join(missing)}")

    data.setdefault("ALGO", "sha256d")
    data.setdefault("USE_GPU", "true")
    data.setdefault("USE_CPU", "false")
    data.setdefault("THREADS", "2")
    data.setdefault("GPU_INTENSITY", "d")
    data.setdefault("POWER_PROFILE", "balanced")
    data.setdefault("EXTRA_ARGS", "")
    return data


def resolve_miner_executable(miner_bin: str) -> str | None:
    if Path(miner_bin).is_file():
        return str(Path(miner_bin))
    return shutil.which(miner_bin)


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        if os.name == "nt":
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True, check=False)
            return str(pid) in out.stdout
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def read_pid() -> int | None:
    if not PID_PATH.exists():
        return None
    text = PID_PATH.read_text(encoding="utf-8", errors="replace").strip()
    return int(text) if text.isdigit() else None


def write_pid(pid: int) -> None:
    PID_PATH.write_text(str(pid), encoding="utf-8")


def remove_pid() -> None:
    if PID_PATH.exists():
        PID_PATH.unlink()


def profile_args(profile: str) -> list[str]:
    return {
        "eco": ["--cpu-priority", "1"],
        "balanced": ["--cpu-priority", "2"],
        "performance": ["--cpu-priority", "5"],
    }.get(profile, [])


def build_command(cfg: dict[str, str]) -> list[str]:
    miner_exe = resolve_miner_executable(cfg["MINER_BIN"])
    if not miner_exe:
        raise RuntimeError(
            "Miner executable not found.\n"
            f"- You set MINER_BIN={cfg['MINER_BIN']}\n"
            "- Install bfgminer/cgminer OR set MINER_BIN to full path, e.g. C:\\miners\\bfgminer.exe"
        )

    cmd = [
        miner_exe,
        "-a",
        cfg["ALGO"],
        "-o",
        cfg["POOL_URL"],
        "-u",
        cfg["POOL_USER"],
        "-p",
        cfg["POOL_PASS"],
    ]
    if cfg["USE_CPU"].lower() == "true":
        cmd.extend(["-t", cfg["THREADS"]])
    if cfg["USE_GPU"].lower() == "true":
        cmd.extend(["--gpu-platform", "0", "--intensity", cfg["GPU_INTENSITY"]])
    cmd.extend(profile_args(cfg["POWER_PROFILE"].lower()))
    if cfg["EXTRA_ARGS"]:
        cmd.extend(shlex.split(cfg["EXTRA_ARGS"]))
    return cmd


def command_start() -> int:
    cfg = parse_config()
    pid = read_pid()
    if pid and process_alive(pid):
        print(f"Miner is already running with PID {pid}.")
        return 0

    cmd = build_command(cfg)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logf = LOG_PATH.open("a", encoding="utf-8", buffering=1)

    kwargs = dict(cwd=str(BASE_DIR), stdout=logf, stderr=subprocess.STDOUT)
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
    else:
        kwargs["start_new_session"] = True

    proc = subprocess.Popen(cmd, **kwargs)
    write_pid(proc.pid)
    print(f"Started miner PID {proc.pid}. Logs: {LOG_PATH}")
    return 0


def command_stop() -> int:
    pid = read_pid()
    if not pid or not process_alive(pid):
        print("Miner is not running.")
        remove_pid()
        return 0

    if os.name == "nt":
        subprocess.run(["taskkill", "/PID", str(pid), "/F"], check=False, capture_output=True)
    else:
        os.kill(pid, signal.SIGTERM)
    remove_pid()
    print("Stopped.")
    return 0


def command_status() -> int:
    pid = read_pid()
    if pid and process_alive(pid):
        print(f"Miner is running with PID {pid}.")
    else:
        print("Miner is not running.")
    return 0


def command_doctor() -> int:
    cfg = parse_config()
    print("== Miner Doctor ==")
    found = resolve_miner_executable(cfg["MINER_BIN"])
    if not found:
        print(
            "[ERR] Miner executable not found.\n"
            f"- MINER_BIN={cfg['MINER_BIN']}\n"
            "- Install bfgminer/cgminer or set full path to .exe"
        )
        return 1
    print(f"[OK] MINER_BIN found: {found}")
    print("[OK] Effective command preview:")
    print(" ".join(shlex.quote(p) for p in build_command(cfg)))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["start", "stop", "status", "doctor"])
    args = parser.parse_args()

    try:
        return {
            "start": command_start,
            "stop": command_stop,
            "status": command_status,
            "doctor": command_doctor,
        }[args.command]()
    except RuntimeError as exc:
        print(str(exc))
        return 1
    except FileNotFoundError as exc:
        print(f"Required file/program was not found: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
