#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk

BASE = Path(__file__).resolve().parent
CONTROL = BASE / "miner_control.py"
CONFIG = BASE / "miner.conf"
LOG = BASE / "miner.log"

FIELDS = [
    ("MINER_BIN", "Miner executable", "bfgminer"),
    ("POOL_URL", "Pool URL", "stratum+tcp://solo.ckpool.org:3333"),
    ("POOL_USER", "Wallet address / worker", "YOUR_BTC_WALLET"),
    ("POOL_PASS", "Pool password", "x"),
    ("USE_GPU", "Use GPU (true/false)", "true"),
    ("USE_CPU", "Use CPU (true/false)", "false"),
    ("THREADS", "CPU threads", "2"),
    ("GPU_INTENSITY", "GPU intensity", "d"),
    ("POWER_PROFILE", "Power profile", "balanced"),
    ("EXTRA_ARGS", "Extra args", ""),
]


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Bitcoin Lottery Miner - Windows Easy Mode")
        self.geometry("980x740")
        self.vars: dict[str, tk.StringVar] = {}
        self._build_ui()
        self.load_config()
        self.auto_fill_miner_if_available()
        self.refresh_status()

    def _build_ui(self) -> None:
        top = ttk.Frame(self, padding=10)
        top.pack(fill=tk.X)
        ttk.Label(
            top,
            text="Fill setup once -> Doctor Check -> Start Mining. If miner missing, click Install/Fix Miner.",
            font=("Segoe UI", 11, "bold"),
        ).pack(anchor="w")

        cfg = ttk.LabelFrame(self, text="Setup", padding=10)
        cfg.pack(fill=tk.X, padx=10, pady=8)

        for idx, (key, label, default) in enumerate(FIELDS):
            ttk.Label(cfg, text=label).grid(row=idx, column=0, sticky="w", padx=5, pady=3)
            v = tk.StringVar(value=default)
            self.vars[key] = v
            ttk.Entry(cfg, textvariable=v, width=70).grid(row=idx, column=1, sticky="we", padx=5, pady=3)

        actions = ttk.Frame(self, padding=10)
        actions.pack(fill=tk.X)
        ttk.Button(actions, text="Install/Fix Miner", command=self.install_or_fix_miner).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Browse for Miner .exe", command=self.choose_miner_exe).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Save Config", command=self.save_config).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Doctor Check", command=lambda: self.run_cmd("doctor")).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Start Mining", command=lambda: self.run_cmd("start")).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Stop Mining", command=lambda: self.run_cmd("stop")).pack(side=tk.LEFT, padx=4)
        ttk.Button(actions, text="Refresh", command=self.refresh_status).pack(side=tk.LEFT, padx=4)

        quick = ttk.Frame(self, padding=(12, 0, 12, 8))
        quick.pack(fill=tk.X)
        ttk.Label(
            quick,
            text="Tip: For payout, set Wallet/Worker to your BTC address if your pool supports wallet-direct payouts.",
        ).pack(anchor="w")

        self.status = tk.StringVar(value="Status: unknown")
        ttk.Label(self, textvariable=self.status, padding=(12, 0)).pack(anchor="w")

        logs_frame = ttk.LabelFrame(self, text="Live Logs", padding=10)
        logs_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        self.logs = scrolledtext.ScrolledText(logs_frame, height=20, wrap=tk.WORD)
        self.logs.pack(fill=tk.BOTH, expand=True)

        self.after(3000, self.periodic_refresh)

    def config_map(self) -> dict[str, str]:
        data = {k: v.get().strip() for k, v in self.vars.items()}
        data["ALGO"] = "sha256d"
        return data

    def save_config(self, quiet: bool = False) -> None:
        data = self.config_map()
        lines = []
        order = [
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
        ]
        for key in order:
            val = data.get(key, "")
            if " " in val:
                val = json.dumps(val)
            lines.append(f"{key}={val}")
        CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")
        if not quiet:
            messagebox.showinfo("Saved", "Configuration saved.")

    def load_config(self) -> None:
        if not CONFIG.exists():
            return
        for raw in CONFIG.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key in self.vars:
                self.vars[key].set(value.strip().strip('"'))

    def auto_fill_miner_if_available(self) -> None:
        current = self.vars["MINER_BIN"].get().strip().lower()
        if current and current not in {"bfgminer", "cgminer", ""}:
            return
        for candidate in self.find_common_miner_locations():
            self.vars["MINER_BIN"].set(str(candidate))
            return

    def find_common_miner_locations(self) -> list[Path]:
        candidates: list[Path] = []
        patterns = [
            Path.home() / "Downloads",
            Path("C:/miners"),
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
        ]
        names = {"bfgminer.exe", "cgminer.exe"}
        for root in patterns:
            if not root.exists():
                continue
            for name in names:
                found = list(root.rglob(name))[:3]
                candidates.extend(found)
        return candidates

    def choose_miner_exe(self) -> None:
        path = filedialog.askopenfilename(
            title="Select miner executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self.vars["MINER_BIN"].set(path)
            self.save_config(quiet=True)
            messagebox.showinfo("Miner selected", f"Using miner executable:\n{path}")

    def install_or_fix_miner(self) -> None:
        msg = (
            "If Start says miner executable not found, install a miner first.\n\n"
            "Recommended steps:\n"
            "1) Open a miner download page\n"
            "2) Download and unzip bfgminer/cgminer\n"
            "3) Click 'Browse for Miner .exe' and select bfgminer.exe or cgminer.exe\n"
            "4) Click Doctor Check then Start Mining\n"
        )
        messagebox.showinfo("Install / Fix Miner", msg)
        if messagebox.askyesno("Open download page?", "Open GitHub search for Windows miner releases now?"):
            webbrowser.open("https://github.com/search?q=bfgminer+windows+release&type=repositories")

    def run_cmd(self, command: str) -> None:
        self.save_config(quiet=True)

        def _worker() -> None:
            p = subprocess.run([sys.executable, str(CONTROL), command], cwd=str(BASE), capture_output=True, text=True, check=False)
            out = (p.stdout + p.stderr).strip() or f"{command} completed"
            if p.returncode == 0:
                self.after(0, lambda: messagebox.showinfo("Miner", out))
            else:
                self.after(0, lambda: messagebox.showerror("Miner Error", out))
            self.after(0, self.refresh_status)

        threading.Thread(target=_worker, daemon=True).start()

    def refresh_status(self) -> None:
        p = subprocess.run([sys.executable, str(CONTROL), "status"], cwd=str(BASE), capture_output=True, text=True, check=False)
        self.status.set(f"Status: {(p.stdout + p.stderr).strip()}")
        if LOG.exists():
            lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()[-120:]
            self.logs.delete("1.0", tk.END)
            self.logs.insert(tk.END, "\n".join(lines))

    def periodic_refresh(self) -> None:
        self.refresh_status()
        self.after(5000, self.periodic_refresh)


if __name__ == "__main__":
    App().mainloop()
