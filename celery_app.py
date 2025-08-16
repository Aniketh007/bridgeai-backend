# celery_app.py
import os
from celery import Celery

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery(
    'ari_backend',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'services.tasks',
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
)

# Add these two lines (recommended)
celery_app.conf.worker_redirect_stdouts = False
# optional: if you do want redirecting but at a specific level
# celery_app.conf.worker_redirect_stdouts_level = "INFO"
