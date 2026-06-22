from celery import Celery

from app.services.storage import validate_storage_provider
from app.settings import settings

validate_storage_provider()


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
    beat_schedule={
        "certificate-monitor-refresh-statuses": {
            "task": "certificate_monitor.refresh_statuses",
            "schedule": settings.CERT_MONITOR_INTERVAL_SECONDS,
        },
        "product-import-cleanup-temp-files": {
            "task": "product_import.cleanup_temp_files",
            "schedule": settings.PRODUCT_IMPORT_CLEANUP_INTERVAL_SECONDS,
        },
        "media-cleanup-orphan-files": {
            "task": "media.cleanup_orphan_files",
            "schedule": settings.MEDIA_ORPHAN_CLEANUP_INTERVAL_SECONDS,
        },
    },
)

celery_app.autodiscover_tasks(["app.tasks"])
