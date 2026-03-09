# Bitcoin Lottery Miner (Noob-Friendly)

## Windows 10: zero-terminal path (click-only)

1. Download the repo ZIP from GitHub.
2. Right-click ZIP -> **Extract All...**
3. Open extracted folder.
4. Double-click **`RUN_ME_WINDOWS.bat`**.
5. A desktop app opens:
   - Fill your pool + wallet info.
   - If needed, click **Install/Fix Miner** then **Browse for Miner .exe**.
   - Click **Save Config**.
   - Click **Doctor Check**.
   - Click **Start Mining**.
6. Leave the app open (or minimize). It shows status + live logs.

If Python is not installed, the batch file shows exactly what to install and where.

By default this app now uses a built-in mining program (`MINER_BIN=internal_py_miner`) so you can start without downloading bfgminer/cgminer.

## If you see “file not found” when pressing Start

That usually means you switched to an external miner and `MINER_BIN` is not installed yet or points to the wrong file.

- Easiest: set `MINER_BIN=internal_py_miner` to use the built-in miner (no external download).
- Or install an external miner binary (for example `bfgminer`/`cgminer`).
- In the app, set **Miner executable** to either:
  - the command name (if it is in PATH), e.g. `bfgminer`
  - OR full path to exe, e.g. `C:\miners\bfgminer.exe`
- Click **Doctor Check** again until it says OK, then click **Start Mining**.

## Important reality check

Mining 1 full BTC in one month on a normal home PC is extraordinarily unlikely. Treat this as hobby lottery mining.

## Files

- `RUN_ME_WINDOWS.bat` - double-click launcher for Windows users.
- `miner/windows_gui.py` - desktop app (Tkinter UI).
- `miner/miner_control.py` - cross-platform control backend (`start/stop/status/doctor`).
- `miner/manager_app.py` - optional browser UI.
- `miner/miner.conf.example` - config template.

## Optional browser UI

If you like browser UI instead of desktop app:

```bash
python3 miner/manager_app.py
```

Then visit `http://127.0.0.1:8080`.


## If Chrome blocks the download

- Click **Install/Fix Miner** in the app to open alternative download/help pages.
- Try Edge or Firefox, then unzip the miner package.
- Click **Browse for Miner .exe** and select `bfgminer.exe` or `cgminer.exe`.
- Before running, scan the downloaded file with your antivirus or VirusTotal.


## Built-in miner mode (no external download)

- Keep `MINER_BIN=internal_py_miner`
- Adjust `THREADS` and `INTERNAL_DIFFICULTY`
- Click **Doctor Check** then **Start Mining**

This built-in miner is educational/lottery-style and logs hashrate and simulated shares. It is not full Bitcoin network mining software.
