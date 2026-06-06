#!/usr/bin/env bash
# VyroPortify single-container start (Render free tier).
# Runs DB migrations on every boot, then the Celery worker as a background
# process and uvicorn in the foreground so the container has one watched
# process. If uvicorn exits Render restarts the container; if Celery dies
# silently the API still answers, and async jobs queue in Redis.
set -euo pipefail

# 1. Apply pending migrations (idempotent — fast no-op when up-to-date).
echo "[start.sh] running alembic upgrade head…"
alembic upgrade head

# 2. Background — Celery worker (concurrency=1 to fit 512 MB RAM).
echo "[start.sh] starting Celery worker in background…"
celery -A app.workers.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --without-gossip --without-mingle --without-heartbeat &

# 3. Foreground — uvicorn.
echo "[start.sh] starting uvicorn on port ${PORT:-8000}…"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
