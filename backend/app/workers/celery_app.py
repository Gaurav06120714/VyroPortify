"""Celery application factory.

Security notes
--------------
- task_serializer / result_serializer / accept_content are all set to "json".
  This prevents pickle deserialization attacks: pickle can execute arbitrary
  Python code when deserializing a crafted payload from a compromised broker.
  JSON is safe because it only reconstructs primitive types.

- worker_hijack_root_logger = False: Celery's default is to take over the
  root logger on worker start, which breaks our structured logging setup and
  can suppress security-relevant log lines. We disable hijacking so our
  log handlers (including any JSON / Sentry handler) remain in control.
"""

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "vyroportify",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.workers.tasks.parse_resume",
        "app.workers.tasks.generate_portfolio",
        # v1.2.0 transactional email + v2.3 PDF export — added late
        # and easy to miss; without these the worker registers the
        # task name but never imports its handler, so .delay() succeeds
        # but the message sits in the queue forever.
        "app.workers.tasks.send_email",
        "app.workers.tasks.export_resume_pdf",
        "app.workers.tasks.deliver_webhook",
    ],
)

import os

celery_app.conf.update(
    # ── Serialization (security-critical) ─────────────────────────────────────
    # Use JSON exclusively. Pickle is the default in older Celery versions and
    # allows remote code execution via a malicious broker message.
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],  # reject any non-JSON content — defense in depth

    # ── Logging ───────────────────────────────────────────────────────────────
    # Do not let Celery take over the root logger; our structured log handlers
    # (Sentry, JSON formatter) must remain registered.
    worker_hijack_root_logger=False,

    # ── Reliability ───────────────────────────────────────────────────────────
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          # ack only after task completes (safer on crash)
    worker_prefetch_multiplier=1, # one task at a time per worker slot
    result_expires=3600,

    # ── Eager mode (UX-04 dev escape hatch) ──────────────────────────────────
    # Set CELERY_TASK_ALWAYS_EAGER=1 to run tasks inline in the API process
    # — useful when a Celery worker isn't running locally. Without this, a
    # POST /portfolio/generate enqueues a task and the page redirects to the
    # /generating poll loop forever because nothing is dequeuing. The flip
    # side: requests now block until the task finishes (~5–15s for portfolio
    # generation). Leave OFF in production; the worker process owns this.
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1",
    task_eager_propagates=True,
)
