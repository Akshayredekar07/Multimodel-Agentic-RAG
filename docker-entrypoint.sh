#!/usr/bin/env bash
set -euo pipefail

uvicorn main:app --host "${API_HOST:-0.0.0.0}" --port "${API_PORT:-8000}" &
api_pid=$!

streamlit run streamlit_app.py \
  --server.address 0.0.0.0 \
  --server.port "${STREAMLIT_SERVER_PORT:-8501}" &
ui_pid=$!

cleanup() {
  kill "$api_pid" "$ui_pid" 2>/dev/null || true
}

trap cleanup SIGINT SIGTERM EXIT

wait -n "$api_pid" "$ui_pid"
