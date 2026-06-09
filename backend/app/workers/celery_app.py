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
        
        "app.workers.tasks.send_email",
        "app.workers.tasks.export_resume_pdf",
        "app.workers.tasks.deliver_webhook",
    ],
)

import os

celery_app.conf.update(
    
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],  

    worker_hijack_root_logger=False,

    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,          
    worker_prefetch_multiplier=1, 
    result_expires=3600,

    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "0") == "1",
    task_eager_propagates=True,
)
