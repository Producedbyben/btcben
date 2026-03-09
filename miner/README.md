# Bitcoin Lottery Miner (Noob-Friendly)

## Windows 10: zero-terminal path (click-only)

1. Download the repo ZIP from GitHub.
2. Right-click ZIP -> **Extract All...**
3. Open extracted folder.
4. Double-click **`RUN_ME_WINDOWS.bat`**.
5. A desktop app opens:
   - Fill your pool + wallet info.
   - Click **Save Config**.
   - Click **Doctor Check**.
   - Click **Start Mining**.
6. Leave the app open (or minimize). It shows status + live logs.

If Python is not installed, the batch file shows exactly what to install and where.

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
