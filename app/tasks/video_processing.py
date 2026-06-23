import asyncio
import socket
from urllib.parse import urlparse

from tortoise import Tortoise

from app.controllers.video_resource import video_resource_controller
from app.core.celery_app import celery_app
from app.log import logger
from app.models.enums import VideoResourceStatus
from app.services import product_video_update_service, video_processing_service
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


def is_celery_broker_reachable(timeout: float = 0.3) -> bool:
    broker_url = settings.CELERY_BROKER_URL
    parsed = urlparse(broker_url)
    if not parsed.hostname:
        return True
    default_ports = {"redis": 6379, "rediss": 6379, "amqp": 5672, "amqps": 5671}
    port = parsed.port or default_ports.get(parsed.scheme)
    if port is None:
        return True
    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout):
            return True
    except OSError:
        return False


def is_celery_worker_available(timeout: float = 0.5) -> bool:
    try:
        inspector = celery_app.control.inspect(timeout=timeout)
        return bool(inspector.ping())
    except Exception as exc:
        logger.warning("inspect celery workers for video processing failed: {}", exc)
        return False


async def process_video_resource(resource_id: int) -> None:
    resource = await video_resource_controller.get(id=resource_id)
    if resource.status == VideoResourceStatus.FAILED and str(resource.error_message or "").strip() == "资源已删除":
        return
    compressed_path = video_processing_service.build_compressed_temp_path()
    await video_resource_controller.update(
        id=resource_id,
        obj_in={
            "status": VideoResourceStatus.PROCESSING,
            "compressed_file_path": compressed_path,
            "error_message": None,
        },
    )
    try:
        await video_processing_service.compress_video(resource.original_file_path, compressed_path)
        refreshed_resource = await video_resource_controller.get(id=resource_id)
        if (
            refreshed_resource.status == VideoResourceStatus.FAILED
            and str(refreshed_resource.error_message or "").strip() == "资源已删除"
        ):
            return
        upload_result = await video_processing_service.upload_compressed_file(
            compressed_path,
            video_processing_service.build_storage_key(),
        )
        await video_resource_controller.update(
            id=resource_id,
            obj_in={
                "status": VideoResourceStatus.UPLOADED,
                "storage_provider": upload_result["storageDriver"],
                "storage_key": upload_result["key"],
                "public_url": upload_result["url"],
                "compressed_size": upload_result["size"],
                "error_message": None,
                "original_file_path": "",
                "compressed_file_path": "",
            },
        )
        video_processing_service.cleanup_file(resource.original_file_path)
        if resource.update_plan_id:
            await product_video_update_service.try_apply_plan(resource.update_plan_id)
    finally:
        video_processing_service.cleanup_file(compressed_path)


@celery_app.task(name="media.compress_video", bind=True, max_retries=3)
def compress_video_resource_task(self, resource_id: int) -> None:
    try:
        asyncio.run(run_in_isolated_tortoise_context(process_video_resource(resource_id)))
    except Exception as exc:
        retries = int(getattr(self.request, "retries", 0))
        if retries < self.max_retries:
            raise self.retry(exc=exc, countdown=3)
        logger.exception("video processing failed permanently: resource_id={}", resource_id)
        asyncio.run(
            run_in_isolated_tortoise_context(
                video_resource_controller.update(
                    id=resource_id,
                    obj_in={
                        "status": VideoResourceStatus.FAILED,
                        "error_message": str(exc),
                        "compressed_file_path": "",
                    },
                )
            )
        )
        resource = asyncio.run(run_in_isolated_tortoise_context(video_resource_controller.get(id=resource_id)))
        if resource.update_plan_id:
            asyncio.run(
                run_in_isolated_tortoise_context(
                    product_video_update_service.mark_plan_failed(resource.update_plan_id, str(exc))
                )
            )
        video_processing_service.cleanup_file(resource.original_file_path)
        video_processing_service.cleanup_file(resource.compressed_file_path)
        asyncio.run(
            run_in_isolated_tortoise_context(
                video_resource_controller.update(
                    id=resource_id,
                    obj_in={"original_file_path": "", "compressed_file_path": ""},
                )
            )
        )


def dispatch_video_processing_task(resource_id: int) -> None:
    if not is_celery_broker_reachable():
        raise RuntimeError(f"celery broker unreachable: {settings.CELERY_BROKER_URL}")
    if not is_celery_worker_available():
        raise RuntimeError("no celery worker available")
    compress_video_resource_task.apply_async(args=[resource_id], retry=False)
