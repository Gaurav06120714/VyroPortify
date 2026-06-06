#!/usr/bin/env bash
# VyroPortify single-container start (Render free tier).
# Runs the Celery worker as a background process and uvicorn in the
# foreground so the container has one watched process. If uvicorn exits
# Render restarts the container; if Celery dies silently the API still
# answers, and async jobs queue in Redis until the next restart.
set -euo pipefail

# Background — Celery worker (concurrency=1 to fit 512 MB RAM).
celery -A app.workers.celery_app worker \
    --loglevel=info \
    --concurrency=1 \
    --without-gossip --without-mingle --without-heartbeat &

# Foreground — uvicorn.
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
