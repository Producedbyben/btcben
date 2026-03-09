# Bitcoin Lottery Miner (Noob-Friendly GPU Background Tool)

This folder gives you a practical **installer + control script + web interface** to run Bitcoin pool mining in the background with your underused GPU/CPU.

> Reality check: finding 1 full BTC in a month on a normal PC is extraordinarily unlikely. Treat this as a lottery-style hobby setup.

## What you get

- `install_and_setup.sh`: guided installer/config wizard for beginners.
- `start_miner.sh`: production wrapper with `start/stop/status/doctor` commands.
- `manager_app.py`: local web control center with:
  - live status, PID, uptime
  - start/stop/doctor actions
  - config editor (pool, payout target, GPU/CPU, power profile)
  - live log tail + hashrate extraction

## Quick start (recommended)

```bash
cd miner
./install_and_setup.sh
./start_miner.sh doctor
python3 manager_app.py
```

Open `http://127.0.0.1:8080`.

## How payout to your wallet works

- Many pools support **wallet-direct usernames** where `POOL_USER` is your Bitcoin wallet address.
- In this setup, set `POOL_USER` to your payout wallet address (or pool worker username if your pool requires account workers).
- Always verify payout method in your pool dashboard.

## Power & control options

You can tune all of these in the web UI or `miner.conf`:

- `USE_GPU` / `USE_CPU`
- `GPU_INTENSITY`
- `THREADS`
- `POWER_PROFILE` (`eco`, `balanced`, `performance`)
- `EXTRA_ARGS` (pass-through for miner-specific advanced flags)

## CLI controls

```bash
./start_miner.sh start
./start_miner.sh status
./start_miner.sh doctor
./start_miner.sh stop
```

## Security tips

- Keep `miner.conf` private (contains pool credentials).
- Keep web UI bound to localhost (`127.0.0.1`) unless you intentionally expose it.
- Expect heat/power usage to increase while mining.
