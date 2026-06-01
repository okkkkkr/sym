import asyncio
import os
import socket
from collections import Counter
from base64 import b64decode
from datetime import datetime
from io import BytesIO
from urllib.parse import urlparse
from zipfile import ZIP_DEFLATED, ZipFile

from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from tortoise.expressions import Q

from app.controllers.product_import import product_import_task_controller
from app.controllers.product_import import product_import_task_item_controller
from app.core.dependency import DependAuth
from app.log import logger
from app.models import User
from app.models.enums import ProductImportStrategy, ProductImportTaskItemStatus, ProductImportTaskStatus
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.product_import import ProductImportTaskActionIn, ProductImportUploadCompleteIn, ProductImportUploadInitIn
from app.services import artifact_storage_service, product_import_upload_service
from app.settings import settings
from app.tasks.product_import import run_product_import, run_product_import_task
from app.utils.excel_export import build_xlsx_content

router = APIRouter(prefix="/import")

PRODUCT_IMPORT_TEMPLATE_FIELDS = [
    "name",
    "category_name",
    "brand_name",
    "desc",
    "tag_names",
    "product_code_custom",
    "status",
    "order",
]

PRODUCT_IMPORT_TEMPLATE_HEADER_LABELS = {
    "name": "名称",
    "category_name": "所属分类",
    "brand_name": "所属品牌",
    "desc": "简介",
    "tag_names": "标签",
    "product_code_custom": "自定义识别码",
    "status": "上架状态",
    "order": "排序",
    "detail_text": "详情文本",
    "detail_description_json": "结构化详情JSON",
}

PRODUCT_IMPORT_TEMPLATE_HEADERS = [
    PRODUCT_IMPORT_TEMPLATE_HEADER_LABELS[field]
    for field in PRODUCT_IMPORT_TEMPLATE_FIELDS
]

PRODUCT_IMPORT_TEMPLATE_SAMPLE_ROW = [
    "示例好物A",
    "示例分类",
    "示例品牌",
    "这是一条示例简介",
    "标签A;标签B",
    "1001",
    "1",
    0,
]

SAMPLE_PNG_BYTES = b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WnW0JkAAAAASUVORK5CYII="
)


def is_celery_broker_reachable(timeout: float = 0.3) -> bool:
    broker_url = settings.CELERY_BROKER_URL
    parsed = urlparse(broker_url)
    if not parsed.hostname:
        return True

    default_ports = {
        "redis": 6379,
        "rediss": 6379,
        "amqp": 5672,
        "amqps": 5671,
    }
    port = parsed.port or default_ports.get(parsed.scheme)
    if port is None:
        return True

    try:
        with socket.create_connection((parsed.hostname, port), timeout=timeout):
            return True
    except OSError:
        return False


def dispatch_product_import_task(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    try:
        if not is_celery_broker_reachable():
            raise ConnectionError(f"celery broker unreachable: {settings.CELERY_BROKER_URL}")
        run_product_import_task.apply_async(args=[task_id, retry_row_nos], retry=False)
    except Exception as exc:
        logger.warning("dispatch product import task via celery failed, fallback to local async run: {}", exc)
        asyncio.create_task(run_product_import(task_id, retry_row_nos=retry_row_nos))


def build_product_import_template_content() -> bytes:
    return build_xlsx_content(
        sheet_title="好物导入模板",
        headers=PRODUCT_IMPORT_TEMPLATE_HEADERS,
        rows=[PRODUCT_IMPORT_TEMPLATE_SAMPLE_ROW],
    )


def build_product_import_example_zip() -> bytes:
    workbook_content = build_xlsx_content(
        sheet_title="好物导入示例",
        headers=PRODUCT_IMPORT_TEMPLATE_HEADERS,
        rows=[PRODUCT_IMPORT_TEMPLATE_SAMPLE_ROW],
    )

    buffer = BytesIO()
    with ZipFile(buffer, "w", compression=ZIP_DEFLATED) as zip_file:
        zip_file.writestr("product.xlsx", workbook_content)
        zip_file.writestr("示例好物A/示例好物A_cover.png", SAMPLE_PNG_BYTES)
        zip_file.writestr("示例好物A/示例好物A_1.png", SAMPLE_PNG_BYTES)
    return buffer.getvalue()


async def build_active_task_summary(task) -> dict:
    data = await task.to_dict()
    creator = await User.get_or_none(id=task.created_by)
    display_name = (creator.alias or creator.username).strip() if creator else ""
    data["created_by_name"] = display_name or f"管理员 #{task.created_by}"
    return data


async def get_active_task_summary(exclude_task_id: int | None = None) -> dict | None:
    task = await product_import_task_controller.get_active_task(exclude_task_id=exclude_task_id)
    if task is None:
        return None
    return await build_active_task_summary(task)


async def build_active_task_conflict(exclude_task_id: int | None = None) -> Fail | None:
    active_task = await get_active_task_summary(exclude_task_id=exclude_task_id)
    if active_task is None:
        return None
    return Fail(
        code=409,
        msg="系统已有进行中的好物导入任务，请等待完成或取消后再试",
        data={"active_task": active_task},
    )


@router.post("/upload-init", summary="初始化好物导入上传")
async def init_product_import_upload(payload: ProductImportUploadInitIn, current_user: User = DependAuth):
    if not payload.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="仅支持上传 ZIP 文件")
    if payload.file_size > settings.PRODUCT_IMPORT_MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超出系统限制")
    if payload.chunk_size > settings.PRODUCT_IMPORT_CHUNK_SIZE:
        raise HTTPException(status_code=400, detail="分片大小超出系统限制")

    try:
        import_strategy = ProductImportStrategy(payload.import_strategy)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="导入策略不合法") from exc

    conflict = await build_active_task_conflict()
    if conflict is not None:
        return conflict

    task = await product_import_task_controller.create_task(
        filename=payload.filename,
        storage_key=f"product-import/raw/pending/{payload.filename}",
        created_by=current_user.id,
        import_strategy=import_strategy,
        status=ProductImportTaskStatus.UPLOADING,
    )
    upload_meta = await product_import_upload_service.init_upload(
        filename=payload.filename,
        file_size=payload.file_size,
        total_chunks=payload.total_chunks,
        chunk_size=payload.chunk_size,
        task_id=task.id,
        created_by=current_user.id,
        import_strategy=import_strategy.value,
    )
    return Success(
        data={
            "upload_id": upload_meta["upload_id"],
            "task_id": task.id,
            "uploaded_chunks": [],
        }
    )


@router.post("/upload-chunk", summary="上传好物导入分片")
async def upload_product_import_chunk(
    upload_id: str = Form(...),
    chunk_index: int = Form(...),
    file: UploadFile = File(...),
    current_user: User = DependAuth,
):
    upload_meta = await product_import_upload_service.get_upload_meta(upload_id)
    if upload_meta["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权操作该上传任务")
    result = await product_import_upload_service.save_chunk(upload_id=upload_id, chunk_index=chunk_index, chunk_file=file)
    return Success(data=result)


@router.get("/upload-status", summary="查询好物导入上传状态")
async def get_product_import_upload_status(
    upload_id: str = Query(..., description="上传ID"),
    current_user: User = DependAuth,
):
    upload_meta = await product_import_upload_service.get_upload_meta(upload_id)
    if upload_meta["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权查看该上传任务")

    uploaded_chunks = await product_import_upload_service.list_uploaded_chunks(upload_id)
    return Success(
        data={
            "upload_id": upload_id,
            "task_id": int(upload_meta["task_id"]),
            "filename": upload_meta["filename"],
            "file_size": int(upload_meta["file_size"]),
            "total_chunks": int(upload_meta["total_chunks"]),
            "chunk_size": int(upload_meta["chunk_size"]),
            "uploaded_chunks": uploaded_chunks,
            "is_complete": len(uploaded_chunks) == int(upload_meta["total_chunks"]),
        }
    )


@router.post("/upload-complete", summary="完成好物导入上传")
async def complete_product_import_upload(payload: ProductImportUploadCompleteIn, current_user: User = DependAuth):
    upload_meta = await product_import_upload_service.get_upload_meta(payload.upload_id)
    if upload_meta["created_by"] != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权完成该上传任务")

    merged_meta = await product_import_upload_service.complete_upload(payload.upload_id)
    task_id = int(merged_meta["task_id"])
    merged_file_path = merged_meta["merged_file_path"]
    conflict = await build_active_task_conflict(exclude_task_id=task_id)
    if conflict is not None:
        return conflict
    try:
        storage_key = await artifact_storage_service.upload_file(
            merged_file_path,
            f"product-import/raw/{task_id}/source.zip",
        )
        await product_import_task_controller.update(
            id=task_id,
            obj_in={
                "storage_key": storage_key,
                "status": ProductImportTaskStatus.QUEUED,
            },
        )
    except Exception as exc:
        await product_import_task_controller.update(
            id=task_id,
            obj_in={
                "status": ProductImportTaskStatus.FAILED,
                "error_message": f"上传文件入库失败：{exc}",
                "finished_at": datetime.now(),
            },
        )
        raise
    finally:
        await product_import_upload_service.cleanup_upload(payload.upload_id)
    dispatch_product_import_task(task_id)
    return Success(
        data={
            "task_id": task_id,
            "storage_key": storage_key,
            "status": ProductImportTaskStatus.QUEUED,
        }
    )


def build_task_search(status: str | None, current_user: User) -> Q:
    query = Q()
    if status:
        query &= Q(status=status)
    if not current_user.is_superuser:
        query &= Q(created_by=current_user.id)
    return query


@router.get("/active-task", summary="查看系统当前进行中的好物导入任务")
async def get_active_product_import_task(current_user: User = DependAuth):
    del current_user
    return Success(data=await get_active_task_summary())


def resolve_task_source_path(storage_key: str) -> str | None:
    stored_path = artifact_storage_service.resolve_stored_path(storage_key)
    if stored_path and os.path.exists(stored_path):
        return stored_path
    if os.path.isabs(storage_key) and os.path.exists(storage_key):
        return storage_key
    relative_path = os.path.join(settings.BASE_DIR, storage_key)
    if os.path.exists(relative_path):
        return relative_path
    return None


def ensure_task_source_available(storage_key: str) -> None:
    if resolve_task_source_path(storage_key):
        return
    raise HTTPException(status_code=400, detail="原始导入包不可用，无法重试")


async def build_task_detail_summary(task_id: int) -> dict:
    items = await product_import_task_item_controller.model.filter(task_id=task_id).all()
    status_counter: Counter[str] = Counter()
    error_counter: Counter[str] = Counter()
    status_order = {
        ProductImportTaskItemStatus.PENDING.value: 0,
        ProductImportTaskItemStatus.SUCCESS.value: 1,
        ProductImportTaskItemStatus.FAILED.value: 2,
        ProductImportTaskItemStatus.SKIPPED.value: 3,
    }

    for item in items:
        status = item.status.value if hasattr(item.status, "value") else str(item.status)
        status_counter[status] += 1
        if status == ProductImportTaskItemStatus.SUCCESS.value or not item.message:
            continue
        for message_part in [part.strip() for part in str(item.message).split(";") if part.strip()]:
            error_counter[message_part] += 1

    status_breakdown = [
        {"status": status, "count": count}
        for status, count in sorted(status_counter.items(), key=lambda item: (status_order.get(item[0], 99), item[0]))
    ]
    error_categories = [
        {"message": message, "count": count}
        for message, count in error_counter.most_common()
    ]
    return {
        "status_breakdown": status_breakdown,
        "error_categories": error_categories,
    }


@router.get("/tasks", summary="查看好物导入任务列表")
async def list_product_import_tasks(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    status: str | None = Query(None, description="任务状态"),
    current_user: User = DependAuth,
):
    total, tasks = await product_import_task_controller.list(
        page=page,
        page_size=page_size,
        search=build_task_search(status, current_user),
        order=["-created_at", "-id"],
    )
    data = [await task.to_dict() for task in tasks]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/task", summary="查看好物导入任务详情")
async def get_product_import_task(task_id: int = Query(..., description="任务ID"), current_user: User = DependAuth):
    task = await product_import_task_controller.get(id=task_id)
    if not current_user.is_superuser and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权查看该任务")
    data = await task.to_dict()
    data["detail_summary"] = await build_task_detail_summary(task_id)
    return Success(data=data)


@router.get("/task/items", summary="查看好物导入任务行级明细")
async def list_product_import_task_items(
    task_id: int = Query(..., description="任务ID"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    status: str | None = Query(None, description="行级状态"),
    current_user: User = DependAuth,
):
    task = await product_import_task_controller.get(id=task_id)
    if not current_user.is_superuser and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权查看该任务")

    search = Q(task_id=task_id)
    if status:
        search &= Q(status=status)
    total, items = await product_import_task_item_controller.list(
        page=page,
        page_size=page_size,
        search=search,
        order=["row_no", "id"],
    )
    data = [await item.to_dict() for item in items]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/task/cancel", summary="取消好物导入任务")
async def cancel_product_import_task(payload: ProductImportTaskActionIn, current_user: User = DependAuth):
    task = await product_import_task_controller.get(id=payload.task_id)
    if not current_user.is_superuser and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权操作该任务")
    if task.status not in {
        ProductImportTaskStatus.PENDING,
        ProductImportTaskStatus.UPLOADING,
        ProductImportTaskStatus.QUEUED,
        ProductImportTaskStatus.RUNNING,
    }:
        raise HTTPException(status_code=400, detail="当前状态下不可取消任务")
    await product_import_task_controller.cancel_task(payload.task_id, message="任务已由用户取消")
    return Success(msg="任务取消成功")


@router.post("/task/retry", summary="重试好物导入任务")
async def retry_product_import_task(payload: ProductImportTaskActionIn, current_user: User = DependAuth):
    task = await product_import_task_controller.get(id=payload.task_id)
    if not current_user.is_superuser and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权操作该任务")
    if task.status not in {
        ProductImportTaskStatus.FAILED,
        ProductImportTaskStatus.WARN,
        ProductImportTaskStatus.CANCELED,
    }:
        raise HTTPException(status_code=400, detail="当前状态下不可重试任务")
    ensure_task_source_available(task.storage_key)
    conflict = await build_active_task_conflict(exclude_task_id=task.id)
    if conflict is not None:
        return conflict

    await product_import_task_item_controller.model.filter(task_id=payload.task_id).delete()
    await product_import_task_controller.update(
        id=payload.task_id,
        obj_in={
            "status": ProductImportTaskStatus.QUEUED,
            "processed_count": 0,
            "success_count": 0,
            "failed_count": 0,
            "progress": 0,
            "error_message": None,
            "result_summary": {},
            "error_report_path": None,
            "started_at": None,
            "finished_at": None,
        },
    )
    dispatch_product_import_task(payload.task_id)
    return Success(msg="任务已重新加入队列")


@router.post("/task/retry-failed", summary="仅重试好物导入失败项")
async def retry_failed_product_import_task(payload: ProductImportTaskActionIn, current_user: User = DependAuth):
    task = await product_import_task_controller.get(id=payload.task_id)
    if not current_user.is_superuser and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权操作该任务")
    if task.status not in {
        ProductImportTaskStatus.FAILED,
        ProductImportTaskStatus.WARN,
        ProductImportTaskStatus.CANCELED,
    }:
        raise HTTPException(status_code=400, detail="当前状态下不可重试失败项")
    ensure_task_source_available(task.storage_key)
    conflict = await build_active_task_conflict()
    if conflict is not None:
        return conflict

    failed_row_nos = await product_import_task_item_controller.model.filter(
        task_id=payload.task_id,
        status=ProductImportTaskItemStatus.FAILED,
    ).order_by("row_no", "id").values_list("row_no", flat=True)
    retry_row_nos = list(dict.fromkeys(failed_row_nos))
    if not retry_row_nos:
        raise HTTPException(status_code=400, detail="当前任务没有可重试的失败项")

    retry_task = await product_import_task_controller.create_task(
        filename=task.filename,
        storage_key=task.storage_key,
        created_by=current_user.id,
        import_strategy=task.import_strategy,
        status=ProductImportTaskStatus.QUEUED,
    )
    await product_import_task_controller.update(
        id=retry_task.id,
        obj_in={
            "result_summary": {
                "retry_source_task_id": task.id,
                "retry_mode": "failed_only",
                "retry_row_count": len(retry_row_nos),
            },
        },
    )
    dispatch_product_import_task(retry_task.id, retry_row_nos=retry_row_nos)
    return Success(
        msg="失败项已重新加入队列",
        data={"task_id": retry_task.id, "retry_row_count": len(retry_row_nos)},
    )


@router.get("/task/errors", summary="下载好物导入错误报告")
async def download_product_import_task_errors(
    task_id: int = Query(..., description="任务ID"),
    current_user: User = DependAuth,
):
    task = await product_import_task_controller.get(id=task_id)
    if not current_user.is_superuser and task.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="当前用户无权查看该任务")
    if not task.error_report_path:
        raise HTTPException(status_code=404, detail="未找到错误报告")

    local_path = artifact_storage_service.resolve_stored_path(task.error_report_path)
    if local_path and os.path.exists(local_path):
        filename = f"product-import-errors-{task_id}.xlsx"
        return StreamingResponse(
            iter([open(local_path, "rb").read()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    if str(task.error_report_path).startswith(("http://", "https://", "/uploads/")):
        return RedirectResponse(url=str(task.error_report_path))
    raise HTTPException(status_code=404, detail="错误报告文件不可用")


@router.get("/template", summary="下载好物导入模板")
async def download_product_import_template():
    content = build_product_import_template_content()
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="product-import-template.xlsx"'},
    )


@router.get("/example", summary="下载好物导入示例ZIP")
async def download_product_import_example():
    content = build_product_import_example_zip()
    return StreamingResponse(
        iter([content]),
        media_type="application/zip",
        headers={"Content-Disposition": 'attachment; filename="product-import-example.zip"'},
    )
