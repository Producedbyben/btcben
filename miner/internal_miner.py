#!/usr/bin/env python3
"""Built-in educational PoW miner (lottery-style simulator, not real Bitcoin block mining)."""
from __future__ import annotations

import argparse
import hashlib
import os
import random
import signal
import threading
import time

RUNNING = True


def _handle_stop(signum, frame):
    global RUNNING
    RUNNING = False


def target_from_difficulty(diff: int) -> int:
    # Lower target => harder. diff around 20-30 gives occasional simulated share hits.
    bits = max(1, min(250, diff))
    return (1 << (256 - bits)) - 1


def format_hs(rate: float) -> str:
    units = ["H/s", "kH/s", "MH/s", "GH/s"]
    u = 0
    while rate >= 1000 and u < len(units) - 1:
        rate /= 1000.0
        u += 1
    return f"{rate:.2f} {units[u]}"


def worker(worker_id: int, base: bytes, target: int, counters: dict):
    nonce = random.randint(0, 2**31)
    local = 0
    found = 0
    while RUNNING:
        payload = base + nonce.to_bytes(8, "little", signed=False)
        h = hashlib.sha256(hashlib.sha256(payload).digest()).digest()
        value = int.from_bytes(h, "big")
        if value <= target:
            found += 1
            print(f"[internal] simulated-share worker={worker_id} nonce={nonce} hash={h.hex()[:24]}...")
        nonce += 1
        local += 1
        if local >= 50_000:
            with counters["lock"]:
                counters["hashes"] += local
                counters["shares"] += found
            local = 0
            found = 0
    if local or found:
        with counters["lock"]:
            counters["hashes"] += local
            counters["shares"] += found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-url", default="internal://sim")
    parser.add_argument("--user", default="wallet")
    parser.add_argument("--threads", type=int, default=max(1, (os.cpu_count() or 2) // 2))
    parser.add_argument("--difficulty", type=int, default=24)
    args = parser.parse_args()

    signal.signal(signal.SIGTERM, _handle_stop)
    signal.signal(signal.SIGINT, _handle_stop)

    target = target_from_difficulty(args.difficulty)
    seed = f"{args.pool_url}|{args.user}|{time.time()}".encode("utf-8")
    base = hashlib.sha256(seed).digest()

    counters = {"hashes": 0, "shares": 0, "lock": threading.Lock()}
    print("[internal] starting built-in miner")
    print("[internal] NOTE: this is an educational lottery miner, not real Bitcoin network mining.")
    print(f"[internal] user={args.user} pool={args.pool_url} threads={args.threads} difficulty={args.difficulty}")

    threads = []
    start = time.time()
    last_hashes = 0
    last_time = start

    for i in range(max(1, args.threads)):
        t = threading.Thread(target=worker, args=(i + 1, base, target, counters), daemon=True)
        t.start()
        threads.append(t)

    while RUNNING:
        time.sleep(5)
        with counters["lock"]:
            total_hashes = counters["hashes"]
            shares = counters["shares"]
        now = time.time()
        interval = max(1e-6, now - last_time)
        rate = (total_hashes - last_hashes) / interval
        uptime = int(now - start)
        print(f"[internal] uptime={uptime}s hashrate={format_hs(rate)} total_hashes={total_hashes} simulated_shares={shares}")
        last_hashes, last_time = total_hashes, now

    for t in threads:
        t.join(timeout=1)

    with counters["lock"]:
        final_hashes = counters["hashes"]
        final_shares = counters["shares"]
    print(f"[internal] stopped total_hashes={final_hashes} simulated_shares={final_shares}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
