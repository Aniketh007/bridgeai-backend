import os
from celery import Celery

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
celery_app = Celery(
    'ari_backend',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[  # <-- add this
        'services.tasks',
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
)