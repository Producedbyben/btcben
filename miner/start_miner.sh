#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/miner.conf"
PID_FILE="${SCRIPT_DIR}/miner.pid"
LOG_FILE="${SCRIPT_DIR}/miner.log"

usage() {
  cat <<USAGE
Usage: $0 <start|stop|status>

Commands:
  start   Start cpuminer in the background using miner.conf
  stop    Stop the running miner process
  status  Show whether a miner process is running
USAGE
}

load_config() {
  if [[ ! -f "${CONFIG_FILE}" ]]; then
    echo "Missing ${CONFIG_FILE}. Copy miner.conf.example to miner.conf and fill in your pool details." >&2
    exit 1
  fi

  # shellcheck source=/dev/null
  source "${CONFIG_FILE}"

  : "${MINER_BIN:?MINER_BIN is required}"
  : "${POOL_URL:?POOL_URL is required}"
  : "${POOL_USER:?POOL_USER is required}"
  : "${POOL_PASS:?POOL_PASS is required}"

  THREADS="${THREADS:-1}"
  EXTRA_ARGS="${EXTRA_ARGS:-}"
}

is_running() {
  [[ -f "${PID_FILE}" ]] && ps -p "$(cat "${PID_FILE}")" > /dev/null 2>&1
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

  echo "Starting miner in background..."
  nohup "${MINER_BIN}" \
    -a sha256d \
    -o "${POOL_URL}" \
    -u "${POOL_USER}" \
    -p "${POOL_PASS}" \
    -t "${THREADS}" \
    ${EXTRA_ARGS} \
    >> "${LOG_FILE}" 2>&1 &

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
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
