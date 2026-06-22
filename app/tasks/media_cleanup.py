import asyncio

from tortoise import Tortoise

from app.core.celery_app import celery_app
from app.services.media_orphan_cleanup import media_orphan_cleanup_service
from app.settings import settings


async def run_in_isolated_tortoise_context(coro):
    if Tortoise._inited:
        await Tortoise.close_connections()
        Tortoise._inited = False
    await Tortoise.init(config=settings.TORTOISE_ORM)
    try:
        return await coro
    finally:
        await Tortoise.close_connections()
        Tortoise._inited = False


@celery_app.task(name="media.cleanup_orphan_files")
def cleanup_orphan_media_files_task() -> dict:
    return asyncio.run(run_in_isolated_tortoise_context(media_orphan_cleanup_service.cleanup_orphan_files()))
