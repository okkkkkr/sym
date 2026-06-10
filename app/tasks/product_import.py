import asyncio
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from tortoise import Tortoise

from app.controllers.product import product_controller
from app.controllers.product_import import product_import_task_controller, product_import_task_item_controller
from app.core.celery_app import celery_app
from app.models.admin import Brand, Category, Tag
from app.models.enums import ProductImportTaskItemStatus, ProductImportTaskStatus
from app.schemas.product_import import ProductImportMaterialSet, ProductImportParsedRow
from app.services import (
    artifact_storage_service,
    media_storage_service,
    product_import_parser_service,
    product_import_upload_service,
    product_import_zip_service,
)
from app.settings import settings
from app.utils.excel_export import build_xlsx_content
from app.utils.product_media import sort_media_keys


async def ensure_tortoise_initialized() -> None:
    if not Tortoise._inited:
        await Tortoise.init(config=settings.TORTOISE_ORM)


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


SAFE_OBJECT_KEY_PART_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_object_key_part(value: str, fallback: str = "file") -> str:
    name = SAFE_OBJECT_KEY_PART_PATTERN.sub("-", str(value or "").strip()).strip("-._")
    return name or fallback


def build_media_object_key(product_name: str, local_path: str, media_type: str) -> str:
    prefix = "items/videos" if media_type == "video" else "items/images"
    product_slug = sanitize_object_key_part(product_name, fallback="product")
    filename = sanitize_object_key_part(Path(local_path).name)
    return f"{prefix}/{product_slug}/{uuid4().hex}_{filename}"


def get_extract_dir(task_id: int) -> str:
    return os.path.join(settings.PRODUCT_IMPORT_TMP_DIR, "extract", str(task_id))


def get_task_extract_owner_id(task) -> int:
    source_task_id = dict(task.result_summary or {}).get("source_extract_task_id")
    try:
        return int(source_task_id) if source_task_id else int(task.id)
    except (TypeError, ValueError):
        return int(task.id)


def get_task_extract_dir(task_id: int) -> str:
    return get_extract_dir(task_id)


async def upload_media_files(product_name: str, file_paths: list[str], media_type: str) -> list[dict[str, str]]:
    uploads: list[dict[str, str]] = []
    media_label = "视频" if media_type == "video" else "图片"
    for file_path in file_paths:
        object_key = build_media_object_key(product_name, file_path, media_type)
        try:
            await media_storage_service.upload_file(file_path, object_key)
        except HTTPException as exc:
            raise HTTPException(
                status_code=exc.status_code,
                detail=f"{media_label}上传失败：{Path(file_path).name}，原因：{exc.detail}",
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=f"{media_label}上传失败：{Path(file_path).name}，原因：{exc}",
            ) from exc
        uploads.append({"path": file_path, "object_key": object_key})
    return uploads


async def generate_error_report(task_id: int) -> str | None:
    items = await product_import_task_item_controller.model.filter(task_id=task_id).order_by("row_no", "id")
    error_rows = []
    for item in items:
        if item.status != ProductImportTaskItemStatus.FAILED:
            continue
        error_rows.append(
            [
                item.row_no,
                item.product_name or "",
                item.category_name or "",
                item.brand_name or "",
                item.status,
                item.message or "",
                "是" if item.duplicate_hint else "否",
            ]
        )

    if not error_rows:
        return None

    content = build_xlsx_content(
        sheet_title="导入错误报告",
        headers=["行号", "好物名称", "分类", "品牌", "状态", "结果信息", "重复提示"],
        rows=error_rows,
    )
    os.makedirs(settings.PRODUCT_IMPORT_TMP_DIR, exist_ok=True)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx", dir=settings.PRODUCT_IMPORT_TMP_DIR) as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        return await artifact_storage_service.upload_file(temp_path, f"product-import/error-report/{task_id}.xlsx")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def is_datetime_recent(value: datetime | None, retention_hours: int) -> bool:
    if value is None:
        return False
    return value.timestamp() > datetime.now().timestamp() - max(1, int(retention_hours)) * 3600


def parse_task_id(value: object) -> int | None:
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


def build_import_summary(task, *, total_rows: int, processed_rows: int, failed_rows: int) -> dict:
    return {
        **dict(task.result_summary or {}),
        "total_count": total_rows,
        "valid_rows": max(processed_rows - failed_rows, 0),
        "invalid_rows": failed_rows,
        "import_started_at": datetime.now().strftime(settings.DATETIME_FORMAT),
    }


async def resolve_import_row(
    row: ProductImportParsedRow,
    *,
    material_set: ProductImportMaterialSet | None,
    category_cache: dict[str, Category | None],
    brand_cache: dict[str, Brand | None],
    tag_cache: dict[str, Tag | None],
) -> ProductImportParsedRow:
    row.errors = list(row.errors)
    row.tag_ids = []
    row.category_id = None
    row.brand_id = None

    if not row.name:
        row.errors.append("名称不能为空")
    if not row.material_dir:
        row.errors.append("素材目录不能为空")
    if not row.category_name:
        row.errors.append("所属分类不能为空")
    if not row.brand_name:
        row.errors.append("所属品牌不能为空")
    if material_set is None:
        row.errors.append("未找到与素材目录对应的素材文件夹")
    elif not material_set.images:
        row.errors.append("素材目录至少需要一张图片")

    if row.category_name:
        if row.category_name not in category_cache:
            category_cache[row.category_name] = await Category.get_or_none(name=row.category_name)
        category = category_cache[row.category_name]
        if category is None:
            row.errors.append("所属分类不存在")
        else:
            row.category_id = category.id

    if row.brand_name:
        if row.brand_name not in brand_cache:
            brand_cache[row.brand_name] = await Brand.get_or_none(name=row.brand_name).prefetch_related("categories")
        brand = brand_cache[row.brand_name]
        if brand is None:
            row.errors.append("所属品牌不存在")
        else:
            row.brand_id = brand.id
            if row.category_id is not None and row.category_id not in {category.id for category in brand.categories}:
                row.errors.append("所属品牌不属于所选分类")

    missing_tags: list[str] = []
    for tag_name in row.tag_names:
        if tag_name not in tag_cache:
            tag_cache[tag_name] = await Tag.get_or_none(name=tag_name)
        tag = tag_cache[tag_name]
        if tag is None:
            missing_tags.append(tag_name)
            continue
        row.tag_ids.append(tag.id)
    if missing_tags:
        row.errors.append(f"以下标签不存在: {', '.join(missing_tags)}")
    row.tag_ids = list(dict.fromkeys(row.tag_ids))
    return row


async def cleanup_product_import_temp_files() -> dict:
    await ensure_tortoise_initialized()
    stats = {
        "enabled": settings.PRODUCT_IMPORT_CLEANUP_ENABLED,
        "deleted_upload_dirs": 0,
        "deleted_extract_dirs": 0,
        "skipped_dirs": 0,
        "deleted_bytes": 0,
        "failures": [],
    }
    if not settings.PRODUCT_IMPORT_CLEANUP_ENABLED:
        return stats

    retention_hours = settings.PRODUCT_IMPORT_CLEANUP_RETENTION_HOURS
    for upload_dir in product_import_upload_service.list_expired_upload_dirs(retention_hours):
        try:
            task_id = parse_task_id(upload_dir["meta"].get("task_id"))
            task = await product_import_task_controller.model.get_or_none(id=task_id) if task_id else None
            if task and task.status in {ProductImportTaskStatus.PENDING, ProductImportTaskStatus.UPLOADING}:
                await product_import_task_controller.update(
                    id=task.id,
                    obj_in={
                        "status": ProductImportTaskStatus.FAILED,
                        "error_message": "上传超时，临时文件已清理",
                        "finished_at": datetime.now(),
                    },
                )
            stats["deleted_bytes"] += product_import_upload_service.cleanup_path(upload_dir["path"])
            stats["deleted_upload_dirs"] += 1
        except Exception as exc:
            stats["failures"].append({"path": upload_dir["path"], "error": str(exc)})

    for extract_dir in product_import_upload_service.list_expired_extract_dirs(retention_hours):
        try:
            task_id = extract_dir["task_id"]
            task = await product_import_task_controller.model.get_or_none(id=task_id) if task_id else None
            if (
                task
                and task.status in {
                    ProductImportTaskStatus.PENDING,
                    ProductImportTaskStatus.RUNNING,
                }
                and is_datetime_recent(task.updated_at, retention_hours)
            ):
                stats["skipped_dirs"] += 1
                continue
            stats["deleted_bytes"] += product_import_upload_service.cleanup_path(extract_dir["path"])
            stats["deleted_extract_dirs"] += 1
        except Exception as exc:
            stats["failures"].append({"path": extract_dir["path"], "error": str(exc)})

    return stats


async def run_product_import(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    await ensure_tortoise_initialized()
    task = await product_import_task_controller.get(id=task_id)
    extract_dir = get_task_extract_dir(get_task_extract_owner_id(task))

    success_count = 0
    failed_count = 0
    processed_count = 0
    canceled = False

    try:
        if (await product_import_task_controller.mark_running(task_id)).status == ProductImportTaskStatus.CANCELED:
            return

        if not os.path.isdir(extract_dir):
            raise HTTPException(status_code=404, detail="未找到导入解压目录")
        await product_import_task_item_controller.model.filter(task_id=task_id).delete()
        workbook_path = os.path.join(extract_dir, "product.xlsx")
        if not os.path.exists(workbook_path):
            raise HTTPException(status_code=404, detail="未找到导入模板文件")
        material_map = product_import_zip_service.scan_materials(extract_dir)
        rows = (await product_import_parser_service.parse(workbook_path)).rows
        retry_row_no_set = set(retry_row_nos or [])
        if retry_row_no_set:
            rows = [row for row in rows if row.row_no in retry_row_no_set]
            if not rows:
                raise HTTPException(status_code=400, detail="未找到可重试的失败项")

        row_item_map = {
            item.row_no: item
            for item in await product_import_task_item_controller.model.filter(task_id=task_id).all()
        }
        total_rows = len(rows)
        category_cache: dict[str, Category | None] = {}
        brand_cache: dict[str, Brand | None] = {}
        tag_cache: dict[str, Tag | None] = {}

        await product_import_task_controller.update_progress(
            task_id,
            total_count=total_rows,
            processed_count=0,
            success_count=0,
            failed_count=0,
            status=ProductImportTaskStatus.RUNNING,
            result_summary=build_import_summary(task, total_rows=total_rows, processed_rows=0, failed_rows=0),
        )

        for row in rows:
            latest_task = await product_import_task_controller.get(id=task_id)
            if latest_task.status == ProductImportTaskStatus.CANCELED:
                canceled = True
                break

            item = row_item_map.get(row.row_no)
            if item is None:
                item = await product_import_task_item_controller.create_item(
                    task_id=task_id,
                    row_no=row.row_no,
                    product_name=row.name,
                    category_name=row.category_name,
                    brand_name=row.brand_name,
                    status=ProductImportTaskItemStatus.PENDING,
                    duplicate_hint=row.duplicate_hint,
                )
                row_item_map[row.row_no] = item
            else:
                item = await product_import_task_item_controller.update(
                    id=item.id,
                    obj_in={
                        "status": ProductImportTaskItemStatus.PENDING,
                        "message": "同步中",
                        "product_id": None,
                    },
                )

            material_set = material_map.get(row.material_dir)
            row = await resolve_import_row(
                row,
                material_set=material_set,
                category_cache=category_cache,
                brand_cache=brand_cache,
                tag_cache=tag_cache,
            )
            if row.errors:
                failed_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_failed(item.id, message="; ".join(row.errors))
                await product_import_task_controller.update_progress(
                    task_id,
                    total_count=total_rows,
                    processed_count=processed_count,
                    success_count=success_count,
                    failed_count=failed_count,
                    status=ProductImportTaskStatus.RUNNING,
                    result_summary=build_import_summary(
                        task,
                        total_rows=total_rows,
                        processed_rows=processed_count,
                        failed_rows=failed_count,
                    ),
                )
                continue

            if material_set is None or not material_set.images:
                failed_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_failed(item.id, message="未找到可同步的素材文件")
                await product_import_task_controller.update_progress(
                    task_id,
                    total_count=total_rows,
                    processed_count=processed_count,
                    success_count=success_count,
                    failed_count=failed_count,
                    status=ProductImportTaskStatus.RUNNING,
                    result_summary=build_import_summary(
                        task,
                        total_rows=total_rows,
                        processed_rows=processed_count,
                        failed_rows=failed_count,
                    ),
                )
                continue

            try:
                image_uploads = await upload_media_files(row.name, material_set.images, "image")
                video_uploads = await upload_media_files(row.name, material_set.videos, "video")
                if (await product_import_task_controller.get(id=task_id)).status == ProductImportTaskStatus.CANCELED:
                    canceled = True
                    processed_count += 1
                    await product_import_task_item_controller.mark_skipped(item.id, message="任务已由用户取消")
                    break
                cover_image_key = next(
                    (
                        uploaded["object_key"]
                        for uploaded in image_uploads
                        if os.path.abspath(uploaded["path"]) == os.path.abspath(material_set.cover_image)
                    ),
                    None,
                )
                image_keys = sort_media_keys(
                    [
                        uploaded["object_key"]
                        for uploaded in image_uploads
                        if os.path.abspath(uploaded["path"]) != os.path.abspath(material_set.cover_image)
                    ]
                )
                video_keys = [video_item["object_key"] for video_item in video_uploads]
                if cover_image_key is None and image_uploads:
                    cover_image_key = image_uploads[0]["object_key"]
                payload = {
                    "category_id": row.category_id,
                    "brand_id": row.brand_id,
                    "name": row.name,
                    "desc": row.desc,
                    "detail_description": row.detail_description,
                    "cover_image_key": cover_image_key,
                    "image_keys": image_keys,
                    "video_keys": video_keys,
                    "status": row.status,
                    "order": row.order,
                }
                try:
                    payload["product_code"] = await product_controller.build_product_code(row.product_code_custom)
                    product = await product_controller.create_with_tags(obj_in=payload, tag_ids=row.tag_ids)
                except HTTPException as exc:
                    raise HTTPException(status_code=exc.status_code, detail=f"好物创建失败，原因：{exc.detail}") from exc
                except Exception as exc:
                    raise HTTPException(status_code=500, detail=f"好物创建失败，原因：{exc}") from exc

                success_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_success(
                    item.id,
                    message="创建成功",
                    product_id=product.id,
                )
            except HTTPException as exc:
                failed_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_failed(item.id, message=str(exc.detail))
            except Exception as exc:
                failed_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_failed(item.id, message=str(exc))

            await product_import_task_controller.update_progress(
                task_id,
                total_count=total_rows,
                processed_count=processed_count,
                success_count=success_count,
                failed_count=failed_count,
                status=ProductImportTaskStatus.RUNNING,
                result_summary=build_import_summary(
                    task,
                    total_rows=total_rows,
                    processed_rows=processed_count,
                    failed_rows=failed_count,
                ),
            )

        error_report_path = await generate_error_report(task_id)
        result_summary = build_import_summary(
            task,
            total_rows=total_rows,
            processed_rows=processed_count,
            failed_rows=failed_count,
        )
        if canceled:
            await product_import_task_controller.update(
                id=task_id,
                obj_in={
                    "status": ProductImportTaskStatus.CANCELED,
                    "processed_count": processed_count,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "progress": 0 if not total_rows else min(100, int((processed_count / total_rows) * 100)),
                    "result_summary": result_summary,
                    "error_report_path": error_report_path,
                    "finished_at": datetime.now(),
                },
            )
        else:
            await product_import_task_controller.finish_task(
                task_id,
                success_count=success_count,
                failed_count=failed_count,
                total_count=total_rows,
                result_summary=result_summary,
                error_report_path=error_report_path,
            )
    except HTTPException as exc:
        await product_import_task_controller.finish_task(
            task_id,
            success_count=success_count,
            failed_count=max(failed_count, 1),
            total_count=processed_count,
            result_summary=build_import_summary(
                task,
                total_rows=processed_count,
                processed_rows=processed_count,
                failed_rows=max(failed_count, 1),
            ),
            error_message=str(exc.detail),
        )
    except Exception as exc:
        await product_import_task_controller.finish_task(
            task_id,
            success_count=success_count,
            failed_count=max(failed_count, 1),
            total_count=processed_count,
            result_summary=build_import_summary(
                task,
                total_rows=processed_count,
                processed_rows=processed_count,
                failed_rows=max(failed_count, 1),
            ),
            error_message=str(exc),
        )

@celery_app.task(name="product_import.run")
def run_product_import_task(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    asyncio.run(run_in_isolated_tortoise_context(run_product_import(task_id, retry_row_nos=retry_row_nos)))


@celery_app.task(name="product_import.cleanup_temp_files")
def cleanup_product_import_temp_files_task() -> dict:
    return asyncio.run(run_in_isolated_tortoise_context(cleanup_product_import_temp_files()))
