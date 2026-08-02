#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="${PROJECT_DIR}/.graph_explorer.pid"

if [[ ! -f "${PID_FILE}" ]]; then
    echo "Graph Explorer is not running (PID file not found)."
    exit 0
fi

APP_PID="$(tr -d '[:space:]' < "${PID_FILE}")"
if [[ ! "${APP_PID}" =~ ^[0-9]+$ ]]; then
    echo "Invalid PID file; removing it without stopping any process."
    rm -f "${PID_FILE}"
    exit 1
fi

if ! kill -0 "${APP_PID}" 2>/dev/null; then
    echo "Graph Explorer process ${APP_PID} is no longer running."
    rm -f "${PID_FILE}"
    exit 0
fi

kill "${APP_PID}"
for _ in {1..50}; do
    if ! kill -0 "${APP_PID}" 2>/dev/null; then
        rm -f "${PID_FILE}"
        echo "Graph Explorer stopped."
        exit 0
    fi
    sleep 0.1
done

echo "Graph Explorer did not stop after 5 seconds; sending SIGKILL."
kill -KILL "${APP_PID}"
rm -f "${PID_FILE}"
echo "Graph Explorer stopped."
