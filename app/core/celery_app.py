from celery import Celery

from app.settings import settings


celery_app = Celery(
    "sym-admin",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Shanghai",
    enable_utc=False,
)

celery_app.autodiscover_tasks(["app.tasks"])