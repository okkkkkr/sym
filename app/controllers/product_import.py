from datetime import datetime

from app.core.crud import CRUDBase
from app.models.import_task import ProductImportTask, ProductImportTaskItem
from app.models.enums import ProductImportStrategy, ProductImportTaskItemStatus, ProductImportTaskStatus


class ProductImportTaskController(CRUDBase[ProductImportTask, dict, dict]):
    def __init__(self):
        super().__init__(model=ProductImportTask)

    async def create_task(
        self,
        *,
        filename: str,
        storage_key: str,
        created_by: int,
        import_strategy: ProductImportStrategy = ProductImportStrategy.CREATE_ONLY,
        status: ProductImportTaskStatus = ProductImportTaskStatus.PENDING,
    ) -> ProductImportTask:
        return await self.create(
            obj_in={
                "filename": filename,
                "storage_key": storage_key,
                "created_by": created_by,
                "import_strategy": import_strategy,
                "status": status,
            }
        )

    async def mark_queued(self, task_id: int) -> ProductImportTask:
        return await self.update(id=task_id, obj_in={"status": ProductImportTaskStatus.QUEUED})

    async def get_active_task(self, exclude_task_id: int | None = None) -> ProductImportTask | None:
        query = self.model.filter(
            status__in=[
                ProductImportTaskStatus.UPLOADING,
                ProductImportTaskStatus.QUEUED,
                ProductImportTaskStatus.RUNNING,
            ]
        )
        if exclude_task_id:
            query = query.exclude(id=exclude_task_id)
        return await query.order_by("created_at", "id").first()

    async def mark_running(self, task_id: int) -> ProductImportTask:
        task = await self.get(id=task_id)
        if task.status == ProductImportTaskStatus.CANCELED:
            return task
        return await self.update(
            id=task_id,
            obj_in={
                "status": ProductImportTaskStatus.RUNNING,
                "started_at": datetime.now(),
            },
        )

    async def update_progress(
        self,
        task_id: int,
        *,
        total_count: int | None = None,
        processed_count: int | None = None,
        success_count: int | None = None,
        failed_count: int | None = None,
        status: ProductImportTaskStatus | None = None,
        result_summary: dict | None = None,
        error_message: str | None = None,
    ) -> ProductImportTask:
        task = await self.get(id=task_id)
        next_total = total_count if total_count is not None else task.total_count
        next_processed = processed_count if processed_count is not None else task.processed_count
        payload = {
            "total_count": next_total,
            "processed_count": next_processed,
            "success_count": success_count if success_count is not None else task.success_count,
            "failed_count": failed_count if failed_count is not None else task.failed_count,
            "progress": 0 if not next_total else min(100, int((next_processed / next_total) * 100)),
        }
        if status is not None and task.status != ProductImportTaskStatus.CANCELED:
            payload["status"] = status
        if result_summary is not None:
            payload["result_summary"] = result_summary
        if error_message is not None:
            payload["error_message"] = error_message
        return await self.update(id=task_id, obj_in=payload)

    async def finish_task(
        self,
        task_id: int,
        *,
        success_count: int,
        failed_count: int,
        total_count: int,
        result_summary: dict | None = None,
        error_message: str | None = None,
        error_report_path: str | None = None,
    ) -> ProductImportTask:
        task = await self.get(id=task_id)
        if task.status == ProductImportTaskStatus.CANCELED:
            return task
        if failed_count <= 0:
            status = ProductImportTaskStatus.SUCCESS
        elif success_count > 0:
            status = ProductImportTaskStatus.WARN
        else:
            status = ProductImportTaskStatus.FAILED

        return await self.update(
            id=task_id,
            obj_in={
                "status": status,
                "total_count": total_count,
                "processed_count": total_count,
                "success_count": success_count,
                "failed_count": failed_count,
                "progress": 100 if total_count else 0,
                "result_summary": result_summary or {},
                "error_message": error_message,
                "error_report_path": error_report_path,
                "finished_at": datetime.now(),
            },
        )

    async def cancel_task(self, task_id: int, message: str | None = None) -> ProductImportTask:
        return await self.update(
            id=task_id,
            obj_in={
                "status": ProductImportTaskStatus.CANCELED,
                "error_message": message,
                "finished_at": datetime.now(),
            },
        )


class ProductImportTaskItemController(CRUDBase[ProductImportTaskItem, dict, dict]):
    def __init__(self):
        super().__init__(model=ProductImportTaskItem)

    async def create_item(
        self,
        *,
        task_id: int,
        row_no: int,
        product_name: str,
        category_name: str | None = None,
        brand_name: str | None = None,
        status: ProductImportTaskItemStatus = ProductImportTaskItemStatus.PENDING,
        message: str | None = None,
        duplicate_hint: bool = False,
        product_id: int | None = None,
    ) -> ProductImportTaskItem:
        return await self.create(
            obj_in={
                "task_id": task_id,
                "row_no": row_no,
                "product_name": product_name,
                "category_name": category_name,
                "brand_name": brand_name,
                "status": status,
                "message": message,
                "duplicate_hint": duplicate_hint,
                "product_id": product_id,
            }
        )

    async def mark_success(self, item_id: int, *, message: str | None = None, product_id: int | None = None):
        return await self.update(
            id=item_id,
            obj_in={
                "status": ProductImportTaskItemStatus.SUCCESS,
                "message": message,
                "product_id": product_id,
            },
        )

    async def mark_failed(self, item_id: int, *, message: str):
        return await self.update(
            id=item_id,
            obj_in={
                "status": ProductImportTaskItemStatus.FAILED,
                "message": message,
            },
        )

    async def mark_skipped(self, item_id: int, *, message: str):
        return await self.update(
            id=item_id,
            obj_in={
                "status": ProductImportTaskItemStatus.SKIPPED,
                "message": message,
            },
        )


product_import_task_controller = ProductImportTaskController()
product_import_task_item_controller = ProductImportTaskItemController()
