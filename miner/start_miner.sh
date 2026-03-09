#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/miner.conf"
PID_FILE="${SCRIPT_DIR}/miner.pid"
LOG_FILE="${SCRIPT_DIR}/miner.log"

usage() {
  cat <<USAGE
Usage: $0 <start|stop|status|doctor>

Commands:
  start    Start configured miner in the background
  stop     Stop the running miner process
  status   Show whether a miner process is running
  doctor   Validate config and show readiness checks
USAGE
}

load_config() {
  if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "Missing ${CONFIG_FILE}. Run ./install_and_setup.sh first." >&2
    exit 1
  fi

  # shellcheck source=/dev/null
  source "${CONFIG_FILE}"

  : "${MINER_BIN:?MINER_BIN is required}"
  : "${POOL_URL:?POOL_URL is required}"
  : "${POOL_USER:?POOL_USER is required}"
  : "${POOL_PASS:?POOL_PASS is required}"

  ALGO="${ALGO:-sha256d}"
  USE_GPU="${USE_GPU:-true}"
  USE_CPU="${USE_CPU:-false}"
  THREADS="${THREADS:-1}"
  POWER_PROFILE="${POWER_PROFILE:-balanced}"
  GPU_INTENSITY="${GPU_INTENSITY:-d}"
  EXTRA_ARGS="${EXTRA_ARGS:-}"
}

is_running() {
  [[ -f "${PID_FILE}" ]] && ps -p "$(cat "${PID_FILE}")" > /dev/null 2>&1
}

build_profile_args() {
  case "${POWER_PROFILE}" in
    eco) echo "--cpu-priority 1" ;;
    balanced) echo "--cpu-priority 2" ;;
    performance) echo "--cpu-priority 5" ;;
    *) echo "" ;;
  esac
}

build_miner_command() {
  local -a cmd
  cmd=("${MINER_BIN}" -a "${ALGO}" -o "${POOL_URL}" -u "${POOL_USER}" -p "${POOL_PASS}")

  if [[ "${USE_CPU}" == "true" ]]; then
    cmd+=( -t "${THREADS}" )
  fi

  if [[ "${USE_GPU}" == "true" ]]; then
    # Common flags for many GPU-capable miners; harmless if ignored.
    cmd+=( --gpu-platform 0 --intensity "${GPU_INTENSITY}" )
  fi

  local profile_args
  profile_args="$(build_profile_args)"

  # shellcheck disable=SC2206
  local profile_arr=( ${profile_args} )
  cmd+=( "${profile_arr[@]}" )

  if [[ -n "${EXTRA_ARGS}" ]]; then
    # shellcheck disable=SC2206
    local extra_arr=( ${EXTRA_ARGS} )
    cmd+=( "${extra_arr[@]}" )
  fi

  printf '%q ' "${cmd[@]}"
}

doctor() {
  load_config
  echo "== Miner Doctor =="
  if command -v "${MINER_BIN}" >/dev/null 2>&1; then
    echo "[OK] MINER_BIN found: ${MINER_BIN}"
  else
    echo "[ERR] MINER_BIN not found in PATH: ${MINER_BIN}"
    exit 1
  fi

  if [[ "${POOL_USER}" =~ ^(bc1|[13])[a-zA-Z0-9]{20,}$ ]]; then
    echo "[OK] POOL_USER looks wallet-like (good for wallet-direct payout pools)."
  else
    echo "[INFO] POOL_USER does not look like a BTC address; this is fine if your pool uses account.worker format."
  fi

  echo "[OK] Ready. Effective command preview:"
  build_miner_command
  echo
}

start_miner() {
  load_config

  if ! command -v "${MINER_BIN}" > /dev/null 2>&1; then
    echo "MINER_BIN '${MINER_BIN}' was not found in PATH." >&2
    exit 1
  fi

  if is_running; then
    echo "Miner is already running with PID $(cat "${PID_FILE}")."
    exit 0
  fi

  local cmd
  cmd="$(build_miner_command)"

  echo "Starting miner in background with profile '${POWER_PROFILE}'..."
  nohup bash -lc "${cmd}" >> "${LOG_FILE}" 2>&1 &

  echo $! > "${PID_FILE}"
  echo "Started miner PID $(cat "${PID_FILE}"). Logs: ${LOG_FILE}"
}

stop_miner() {
  if ! is_running; then
    echo "Miner is not running."
    rm -f "${PID_FILE}"
    exit 0
  fi

  local pid
  pid="$(cat "${PID_FILE}")"
  echo "Stopping miner PID ${pid}..."
  kill "${pid}"
  rm -f "${PID_FILE}"
  echo "Stopped."
}

status_miner() {
  if is_running; then
    echo "Miner is running with PID $(cat "${PID_FILE}")."
  else
    echo "Miner is not running."
  fi
}

main() {
  local cmd="${1:-}"
  case "${cmd}" in
    start) start_miner ;;
    stop) stop_miner ;;
    status) status_miner ;;
    doctor) doctor ;;
    *) usage; exit 1 ;;
  esac
}

main "$@"
