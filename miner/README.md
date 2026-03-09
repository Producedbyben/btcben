# Background Bitcoin Miner (Pool Worker)

This setup runs a SHA-256d miner (`cpuminer`) in the background using your own pool credentials.

## Important reality check

Mining **1 full BTC in one month on a normal PC is not realistic**. Bitcoin mining is highly competitive and usually done with specialized ASIC hardware. This folder gives you a background worker you can run, but it cannot guarantee finding 1 BTC.

## 1) Install a miner binary

You need a SHA-256d-capable miner such as `cpuminer-opt`/`cpuminer`.

Example (Debian/Ubuntu-like systems):

```bash
sudo apt update
sudo apt install -y cpuminer
```

If your distro package is outdated, build/install a modern cpuminer variant and ensure its executable is available in your `PATH`.

## 2) Configure pool credentials

```bash
cd miner
cp miner.conf.example miner.conf
```

Edit `miner.conf` and set:
- `POOL_URL`
- `POOL_USER`
- `POOL_PASS`
- `THREADS`

## 3) Start in background

```bash
./start_miner.sh start
```

Check status:

```bash
./start_miner.sh status
```

Stop it:

```bash
./start_miner.sh stop
```

Logs are written to `miner/miner.log`.

## Tips

- Start with a small thread count so your PC stays responsive.
- Use pool stats to monitor expected payout.
- Consider power cost vs. expected mining revenue.
