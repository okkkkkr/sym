import asyncio

from tortoise import Tortoise

from app.models.enums import ProductImportTaskStatus
from app.models.import_task import ProductImportTask
from app.settings import settings


async def main() -> int:
    await Tortoise.init(config=settings.TORTOISE_ORM)
    try:
        active_statuses = [
            ProductImportTaskStatus.UPLOADING,
            ProductImportTaskStatus.PENDING,
            ProductImportTaskStatus.VALIDATING,
            ProductImportTaskStatus.QUEUED,
            ProductImportTaskStatus.RUNNING,
        ]
        tasks = await ProductImportTask.filter(status__in=active_statuses).values(
            "id", "filename", "status", "created_by"
        )
        if not tasks:
            print("No active product ZIP import tasks.")
            return 0
        for task in tasks:
            print(
                f"ACTIVE id={task['id']} status={task['status']} creator={task['created_by']} file={task['filename']}"
            )
        print("Deployment blocked: finish or cancel every active import task first.")
        return 1
    finally:
        await Tortoise.close_connections()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
