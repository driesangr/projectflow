#!/bin/sh
# ─────────────────────────────────────────────────────────────────────────────
# Project Flow – Backend entrypoint
#
# 1. Runs Alembic migrations (blocks startup until DB is ready)
# 2. Starts uvicorn; any extra args (e.g. --reload) are forwarded
# ─────────────────────────────────────────────────────────────────────────────
set -e

echo "[entrypoint] Running database migrations..."
alembic upgrade head

echo "[entrypoint] Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 "$@"
