import asyncio

from tortoise import Tortoise

from app.core.celery_app import celery_app
from app.services.certificate_monitor import certificate_monitor_service
from app.settings import settings


async def _run_refresh_statuses() -> list[dict]:
    if not Tortoise._inited:
        await Tortoise.init(config=settings.TORTOISE_ORM)
    try:
        return await certificate_monitor_service.refresh_statuses()
    finally:
        if Tortoise._inited:
            await Tortoise.close_connections()
            Tortoise._inited = False


@celery_app.task(name="certificate_monitor.refresh_statuses")
def refresh_certificate_statuses():
    if not settings.CERT_MONITOR_ENABLED:
        return []
    return asyncio.run(_run_refresh_statuses())
