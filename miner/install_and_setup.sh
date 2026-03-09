#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/miner.conf"
EXAMPLE_FILE="${SCRIPT_DIR}/miner.conf.example"

bold() { printf "\033[1m%s\033[0m\n" "$*"; }
info() { printf "[INFO] %s\n" "$*"; }
warn() { printf "[WARN] %s\n" "$*"; }

prompt() {
  local question="$1" default="${2:-}" value
  read -r -p "${question}${default:+ [${default}]}: " value
  echo "${value:-$default}"
}

install_hint() {
  bold "Install miner binary"
  if command -v bfgminer >/dev/null 2>&1; then
    info "bfgminer already detected."
    return
  fi

  warn "No bfgminer found. For best results use a GPU-capable miner."
  if command -v apt >/dev/null 2>&1; then
    info "Try: sudo apt update && sudo apt install -y bfgminer"
  elif command -v dnf >/dev/null 2>&1; then
    info "Try: sudo dnf install bfgminer"
  elif command -v brew >/dev/null 2>&1; then
    info "Try: brew install bfgminer"
  else
    info "Install bfgminer/cgminer manually, then rerun this setup."
  fi
}

main() {
  bold "=== Bitcoin Lottery Miner: Guided Setup ==="
  install_hint

  local miner_bin pool_url wallet_or_user pool_pass use_gpu use_cpu threads intensity profile extra internal_diff

  miner_bin="$(prompt 'Miner binary to run (internal_py_miner for built-in)' 'internal_py_miner')"
  pool_url="$(prompt 'Pool URL (stratum+tcp://...)' 'stratum+tcp://solo.ckpool.org:3333')"
  wallet_or_user="$(prompt 'Wallet address or pool worker username (payout target)' 'YOUR_BTC_WALLET')"
  pool_pass="$(prompt 'Pool password' 'x')"
  use_gpu="$(prompt 'Use GPU? (true/false)' 'true')"
  use_cpu="$(prompt 'Use CPU as well? (true/false)' 'false')"
  threads="$(prompt 'CPU threads if enabled' '2')"
  intensity="$(prompt 'GPU intensity (d or number, miner-specific)' 'd')"
  profile="$(prompt 'Power profile (eco/balanced/performance)' 'balanced')"
  extra="$(prompt 'Extra args (optional)' '')"
  internal_diff="$(prompt 'Built-in miner difficulty (higher=harder)' '24')"

  cat > "${CONFIG_FILE}" <<CFG
MINER_BIN=${miner_bin}
ALGO=sha256d
POOL_URL=${pool_url}
POOL_USER=${wallet_or_user}
POOL_PASS=${pool_pass}
USE_GPU=${use_gpu}
USE_CPU=${use_cpu}
THREADS=${threads}
GPU_INTENSITY=${intensity}
POWER_PROFILE=${profile}
EXTRA_ARGS="${extra}"
INTERNAL_DIFFICULTY=${internal_diff}
CFG

  chmod 600 "${CONFIG_FILE}" || true
  bold "Saved ${CONFIG_FILE}"
  info "Next steps:"
  info "1) ./start_miner.sh doctor"
  info "2) ./start_miner.sh start"
  info "3) python3 manager_app.py  # open UI at http://127.0.0.1:8080"

  if [[ -f "${EXAMPLE_FILE}" ]]; then
    info "Reference template remains at ${EXAMPLE_FILE}"
  fi
}

main "$@"
