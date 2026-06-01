import asyncio
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from tortoise import Tortoise

from app.controllers.product import product_controller
from app.controllers.product_import import product_import_task_controller, product_import_task_item_controller
from app.core.celery_app import celery_app
from app.models.enums import ProductImportTaskItemStatus, ProductImportTaskStatus
from app.services import (
    artifact_storage_service,
    media_storage_service,
    product_import_parser_service,
    product_import_upload_service,
    product_import_zip_service,
)
from app.settings import settings
from app.utils.excel_export import build_xlsx_content


async def ensure_tortoise_initialized() -> None:
    if not Tortoise._inited:
        await Tortoise.init(config=settings.TORTOISE_ORM)


SAFE_OBJECT_KEY_PART_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_object_key_part(value: str, fallback: str = "file") -> str:
    name = SAFE_OBJECT_KEY_PART_PATTERN.sub("-", str(value or "").strip()).strip("-._")
    return name or fallback


def build_media_object_key(product_name: str, local_path: str, media_type: str) -> str:
    prefix = "items/videos" if media_type == "video" else "items/images"
    product_slug = sanitize_object_key_part(product_name, fallback="product")
    filename = sanitize_object_key_part(Path(local_path).name)
    return f"{prefix}/{product_slug}/{uuid4().hex}_{filename}"


async def upload_media_files(product_name: str, file_paths: list[str], media_type: str) -> list[dict[str, str]]:
    uploads: list[dict[str, str]] = []
    media_label = "视频" if media_type == "video" else "图片"
    for file_path in file_paths:
        try:
            url = await media_storage_service.upload_file(
                file_path,
                build_media_object_key(product_name, file_path, media_type),
            )
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
        uploads.append({"path": file_path, "url": url})
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


async def cleanup_product_import_upload(zip_path: str) -> None:
    upload_dir = Path(zip_path).resolve().parent
    base_dir = Path(settings.PRODUCT_IMPORT_TMP_DIR).resolve()

    try:
        upload_dir.relative_to(base_dir)
    except ValueError:
        return

    meta_path = upload_dir / "meta.json"
    if not meta_path.exists():
        return

    await product_import_upload_service.cleanup_upload(upload_dir.name)


def resolve_task_zip_path(storage_key: str) -> str:
    stored_path = artifact_storage_service.resolve_stored_path(storage_key)
    if stored_path:
        return stored_path
    if os.path.isabs(storage_key):
        return storage_key
    return os.path.join(settings.BASE_DIR, storage_key)


def is_datetime_recent(value: datetime | None, retention_hours: int) -> bool:
    if value is None:
        return False
    return value.timestamp() > datetime.now().timestamp() - max(1, int(retention_hours)) * 3600


def parse_task_id(value: object) -> int | None:
    try:
        return int(value) if value else None
    except (TypeError, ValueError):
        return None


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
                and task.status == ProductImportTaskStatus.RUNNING
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
    zip_path = resolve_task_zip_path(task.storage_key)

    extract_dir = ""
    success_count = 0
    failed_count = 0
    processed_count = 0
    canceled = False
    retry_row_no_set = set(retry_row_nos or [])
    rows = []
    total_rows = 0
    valid_rows = 0
    invalid_rows = 0

    try:
        if (await product_import_task_controller.mark_running(task_id)).status == ProductImportTaskStatus.CANCELED:
            return

        product_import_zip_service.validate_zip(zip_path)
        extract_dir = product_import_zip_service.extract_to_temp(zip_path, task_id)
        workbook_path = os.path.join(extract_dir, "product.xlsx")
        material_map = product_import_zip_service.scan_materials(extract_dir)
        parse_result = await product_import_parser_service.parse(workbook_path)
        rows = parse_result.rows
        if retry_row_no_set:
            rows = [row for row in rows if row.row_no in retry_row_no_set]
            if not rows:
                raise HTTPException(status_code=400, detail="未找到可重试的失败项")

        total_rows = len(rows)
        valid_rows = sum(1 for row in rows if not row.errors)
        invalid_rows = total_rows - valid_rows

        await product_import_task_controller.update_progress(
            task_id,
            total_count=total_rows,
            processed_count=0,
            success_count=0,
            failed_count=0,
            status=ProductImportTaskStatus.RUNNING,
        )

        for row in rows:
            latest_task = await product_import_task_controller.get(id=task_id)
            if latest_task.status == ProductImportTaskStatus.CANCELED:
                canceled = True
                break

            item = await product_import_task_item_controller.create_item(
                task_id=task_id,
                row_no=row.row_no,
                product_name=row.name,
                category_name=row.category_name,
                brand_name=row.brand_name,
                status=ProductImportTaskItemStatus.PENDING,
                duplicate_hint=row.duplicate_hint,
            )

            material_set = material_map.get(row.name)
            row_errors = list(row.errors)
            if material_set is None:
                row_errors.append("未找到与名称对应的素材目录")
            else:
                if not material_set.images:
                    row_errors.append("素材目录至少需要一张图片")
                if not material_set.cover_image:
                    row_errors.append("未能识别封面图")

            if row_errors:
                failed_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_failed(item.id, message="; ".join(row_errors))
                await product_import_task_controller.update_progress(
                    task_id,
                    total_count=total_rows,
                    processed_count=processed_count,
                    success_count=success_count,
                    failed_count=failed_count,
                    status=ProductImportTaskStatus.RUNNING,
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
                image_urls = [item["url"] for item in image_uploads]
                video_urls = [item["url"] for item in video_uploads]
                cover_image_url = next(
                    (
                        item["url"]
                        for item in image_uploads
                        if os.path.abspath(item["path"]) == os.path.abspath(material_set.cover_image)
                    ),
                    None,
                )
                if cover_image_url is None and image_urls:
                    cover_image_url = image_urls[0]
                payload = {
                    "category_id": row.category_id,
                    "brand_id": row.brand_id,
                    "name": row.name,
                    "desc": row.desc,
                    "detail_description": row.detail_description,
                    "cover_image_url": cover_image_url,
                    "image_urls": image_urls,
                    "video_urls": video_urls,
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
            )

        error_report_path = await generate_error_report(task_id)
        result_summary = {
            **dict(task.result_summary or {}),
            "total_count": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
        }
        if canceled:
            await product_import_task_controller.update(
                id=task_id,
                obj_in={
                    "status": ProductImportTaskStatus.CANCELED,
                    "processed_count": processed_count,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "progress": 0
                    if not total_rows
                    else min(100, int((processed_count / total_rows) * 100)),
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
            total_count=total_rows or processed_count,
            result_summary={
                **dict(task.result_summary or {}),
                "total_count": total_rows or processed_count,
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
            },
            error_message=str(exc.detail),
        )
    except Exception as exc:
        await product_import_task_controller.finish_task(
            task_id,
            success_count=success_count,
            failed_count=max(failed_count, 1),
            total_count=total_rows or processed_count,
            result_summary={
                **dict(task.result_summary or {}),
                "total_count": total_rows or processed_count,
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
            },
            error_message=str(exc),
        )
    finally:
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        if zip_path and os.path.exists(zip_path):
            await cleanup_product_import_upload(zip_path)


@celery_app.task(name="product_import.run")
def run_product_import_task(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    asyncio.run(run_product_import(task_id, retry_row_nos=retry_row_nos))


@celery_app.task(name="product_import.cleanup_temp_files")
def cleanup_product_import_temp_files_task() -> dict:
    return asyncio.run(cleanup_product_import_temp_files())
