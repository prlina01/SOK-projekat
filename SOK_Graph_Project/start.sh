#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SOK_GRAPH_VENV:-${PROJECT_DIR}/.venv}"
HOST="${SOK_GRAPH_HOST:-127.0.0.1}"
PORT="${SOK_GRAPH_PORT:-5000}"
PID_FILE="${PROJECT_DIR}/.graph_explorer.pid"
LOG_FILE="${PROJECT_DIR}/.graph_explorer.log"

if [[ -f "${PID_FILE}" ]]; then
    EXISTING_PID="$(tr -d '[:space:]' < "${PID_FILE}")"
    if [[ "${EXISTING_PID}" =~ ^[0-9]+$ ]] && kill -0 "${EXISTING_PID}" 2>/dev/null; then
        echo "Graph Explorer is already running (PID ${EXISTING_PID})."
        echo "Open http://${HOST}:${PORT}/"
        exit 0
    fi
    rm -f "${PID_FILE}"
fi

install_components() {
    if command -v uv >/dev/null 2>&1; then
        uv pip install --python "${VENV_DIR}/bin/python" \
            -e "${PROJECT_DIR}/api" \
            -e "${PROJECT_DIR}/platform" \
            -e "${PROJECT_DIR}/plugins/csv_data_source" \
            -e "${PROJECT_DIR}/plugins/json_data_source" \
            -e "${PROJECT_DIR}/plugins/simple_visualizer" \
            -e "${PROJECT_DIR}/plugins/block_visualizer" \
            -e "${PROJECT_DIR}/graph_explorer"
    else
        "${VENV_DIR}/bin/python" -m pip install \
            -e "${PROJECT_DIR}/api" \
            -e "${PROJECT_DIR}/platform" \
            -e "${PROJECT_DIR}/plugins/csv_data_source" \
            -e "${PROJECT_DIR}/plugins/json_data_source" \
            -e "${PROJECT_DIR}/plugins/simple_visualizer" \
            -e "${PROJECT_DIR}/plugins/block_visualizer" \
            -e "${PROJECT_DIR}/graph_explorer"
    fi
}

if [[ ! -x "${VENV_DIR}/bin/python" ]]; then
    echo "Creating virtual environment at ${VENV_DIR}..."
    if command -v uv >/dev/null 2>&1; then
        uv venv "${VENV_DIR}"
    else
        python3 -m venv "${VENV_DIR}"
    fi
    install_components
elif [[ ! -x "${VENV_DIR}/bin/sok-graph-explorer" ]] || \
    ! "${VENV_DIR}/bin/python" -c "import flask, graph_explorer, service, graph" >/dev/null 2>&1; then
    echo "Installing Graph Explorer components..."
    install_components
fi

echo "Starting Graph Explorer on http://${HOST}:${PORT}/ ..."
SOK_GRAPH_HOST="${HOST}" SOK_GRAPH_PORT="${PORT}" \
    nohup "${VENV_DIR}/bin/sok-graph-explorer" >"${LOG_FILE}" 2>&1 &
APP_PID=$!
echo "${APP_PID}" > "${PID_FILE}"

for _ in {1..30}; do
    if ! kill -0 "${APP_PID}" 2>/dev/null; then
        echo "Graph Explorer failed to start. Log output:"
        sed -n '1,120p' "${LOG_FILE}"
        rm -f "${PID_FILE}"
        exit 1
    fi

    if "${VENV_DIR}/bin/python" -c \
        "import urllib.request; urllib.request.urlopen('http://${HOST}:${PORT}/', timeout=1)" \
        >/dev/null 2>&1; then
        echo "Graph Explorer is running (PID ${APP_PID})."
        echo "Open http://${HOST}:${PORT}/"
        echo "Log: ${LOG_FILE}"
        exit 0
    fi
    sleep 0.2
done

echo "The process started, but the web server did not become ready in time."
echo "Check ${LOG_FILE}"
kill "${APP_PID}" 2>/dev/null || true
rm -f "${PID_FILE}"
exit 1
