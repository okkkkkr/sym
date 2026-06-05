import asyncio
import json
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
from app.log import logger
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


def get_validation_snapshot_path(task_id: int) -> str:
    return os.path.join(get_extract_dir(task_id), "validation.json")


def serialize_row(row: ProductImportParsedRow) -> dict:
    return row.model_dump(mode="json")


def deserialize_row(payload: dict) -> ProductImportParsedRow:
    return ProductImportParsedRow.model_validate(payload)


def serialize_material_set(material_set: ProductImportMaterialSet) -> dict:
    return material_set.model_dump(mode="json")


def deserialize_material_set(payload: dict) -> ProductImportMaterialSet:
    return ProductImportMaterialSet.model_validate(payload)


def write_validation_snapshot(task_id: int, rows: list[ProductImportParsedRow], material_map: dict[str, ProductImportMaterialSet]) -> None:
    extract_dir = get_extract_dir(task_id)
    os.makedirs(extract_dir, exist_ok=True)
    with open(get_validation_snapshot_path(task_id), "w", encoding="utf-8") as snapshot_file:
        json.dump(
            {
                "rows": [serialize_row(row) for row in rows],
                "material_map": {
                    directory_name: serialize_material_set(material_set)
                    for directory_name, material_set in material_map.items()
                },
            },
            snapshot_file,
            ensure_ascii=False,
        )


def read_validation_snapshot(task_id: int) -> tuple[list[ProductImportParsedRow], dict[str, ProductImportMaterialSet]]:
    snapshot_path = get_validation_snapshot_path(task_id)
    if not os.path.exists(snapshot_path):
        raise HTTPException(status_code=400, detail="未找到合法性检测结果，请重新发起导入")

    with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
        payload = json.load(snapshot_file)

    rows = [deserialize_row(item) for item in payload.get("rows", [])]
    material_map = {
        directory_name: deserialize_material_set(item)
        for directory_name, item in dict(payload.get("material_map") or {}).items()
    }
    return rows, material_map


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


def build_validation_summary(task, *, total_rows: int, valid_rows: int, invalid_rows: int) -> dict:
    return {
        **dict(task.result_summary or {}),
        "validation_total_rows": total_rows,
        "validation_passed_rows": valid_rows,
        "validation_failed_rows": invalid_rows,
        "validation_finished_at": datetime.now().strftime(settings.DATETIME_FORMAT),
    }


def dispatch_product_import_after_validation(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    try:
        run_product_import_task.apply_async(args=[task_id, retry_row_nos], retry=False)
    except Exception as exc:
        logger.warning("dispatch validated product import task via celery failed, fallback to local async run: {}", exc)
        asyncio.create_task(run_product_import(task_id, retry_row_nos=retry_row_nos))


async def create_validation_items(task_id: int, rows: list[ProductImportParsedRow], material_map: dict[str, ProductImportMaterialSet]) -> tuple[int, int]:
    valid_rows = 0
    invalid_rows = 0

    for row in rows:
        row_errors = list(row.errors)
        material_set = material_map.get(row.material_dir)
        if material_set is None:
            row_errors.append("未找到与素材目录对应的素材文件夹")
        elif not material_set.images:
            row_errors.append("素材目录至少需要一张图片")

        item = await product_import_task_item_controller.create_item(
            task_id=task_id,
            row_no=row.row_no,
            product_name=row.name,
            category_name=row.category_name,
            brand_name=row.brand_name,
            status=ProductImportTaskItemStatus.FAILED if row_errors else ProductImportTaskItemStatus.VALIDATED,
            message="; ".join(row_errors) if row_errors else "合法性检测通过",
            duplicate_hint=row.duplicate_hint,
        )
        if row_errors:
            invalid_rows += 1
            continue
        await product_import_task_item_controller.mark_validated(item.id, message="合法性检测通过")
        valid_rows += 1

    return valid_rows, invalid_rows


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
                    ProductImportTaskStatus.VALIDATING,
                    ProductImportTaskStatus.QUEUED,
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


async def run_product_import_validation(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    await ensure_tortoise_initialized()
    task = await product_import_task_controller.get(id=task_id)
    zip_path = resolve_task_zip_path(task.storage_key)
    extract_dir = ""
    should_cleanup_extract_dir = True
    retry_row_no_set = set(retry_row_nos or [])
    total_rows = 0
    valid_rows = 0
    invalid_rows = 0

    try:
        if (await product_import_task_controller.mark_validating(task_id)).status == ProductImportTaskStatus.CANCELED:
            return

        await product_import_task_item_controller.model.filter(task_id=task_id).delete()
        product_import_zip_service.validate_zip(zip_path)
        extract_dir = product_import_zip_service.extract_to_temp(zip_path, task_id)
        workbook_path = os.path.join(extract_dir, "product.xlsx")
        material_map = product_import_zip_service.scan_materials(extract_dir)
        rows = (await product_import_parser_service.parse(workbook_path)).rows
        if retry_row_no_set:
            rows = [row for row in rows if row.row_no in retry_row_no_set]
            if not rows:
                raise HTTPException(status_code=400, detail="未找到可重试的失败项")

        total_rows = len(rows)
        valid_rows, invalid_rows = await create_validation_items(task_id, rows, material_map)
        result_summary = build_validation_summary(
            task,
            total_rows=total_rows,
            valid_rows=valid_rows,
            invalid_rows=invalid_rows,
        )
        error_report_path = await generate_error_report(task_id)
        if (await product_import_task_controller.get(id=task_id)).status == ProductImportTaskStatus.CANCELED:
            return

        if invalid_rows > 0:
            await product_import_task_controller.update(
                id=task_id,
                obj_in={
                    "status": ProductImportTaskStatus.VALIDATION_FAILED,
                    "total_count": total_rows,
                    "processed_count": total_rows,
                    "success_count": valid_rows,
                    "failed_count": invalid_rows,
                    "progress": 100 if total_rows else 0,
                    "result_summary": result_summary,
                    "error_message": "合法性校验不通过，请修正后重新上传",
                    "error_report_path": error_report_path,
                    "finished_at": datetime.now(),
                },
            )
            return

        write_validation_snapshot(task_id, rows, material_map)
        should_cleanup_extract_dir = False
        await product_import_task_controller.update(
            id=task_id,
            obj_in={
                "status": ProductImportTaskStatus.QUEUED,
                "total_count": total_rows,
                "processed_count": 0,
                "success_count": 0,
                "failed_count": 0,
                "progress": 0,
                "result_summary": result_summary,
                "error_message": None,
                "error_report_path": error_report_path,
                "finished_at": None,
            },
        )
        dispatch_product_import_after_validation(task_id, retry_row_nos=retry_row_nos)
    except HTTPException as exc:
        if (await product_import_task_controller.get(id=task_id)).status == ProductImportTaskStatus.CANCELED:
            return
        error_report_path = await generate_error_report(task_id)
        await product_import_task_controller.update(
            id=task_id,
            obj_in={
                "status": ProductImportTaskStatus.VALIDATION_FAILED,
                "total_count": total_rows,
                "processed_count": total_rows,
                "success_count": valid_rows,
                "failed_count": max(invalid_rows, 1),
                "progress": 100 if total_rows else 0,
                "result_summary": build_validation_summary(
                    task,
                    total_rows=total_rows,
                    valid_rows=valid_rows,
                    invalid_rows=max(invalid_rows, 1 if total_rows or valid_rows else 0),
                ),
                "error_message": str(exc.detail),
                "error_report_path": error_report_path,
                "finished_at": datetime.now(),
            },
        )
    except Exception as exc:
        if (await product_import_task_controller.get(id=task_id)).status == ProductImportTaskStatus.CANCELED:
            return
        error_report_path = await generate_error_report(task_id)
        await product_import_task_controller.update(
            id=task_id,
            obj_in={
                "status": ProductImportTaskStatus.VALIDATION_FAILED,
                "total_count": total_rows,
                "processed_count": total_rows,
                "success_count": valid_rows,
                "failed_count": max(invalid_rows, 1),
                "progress": 100 if total_rows else 0,
                "result_summary": build_validation_summary(
                    task,
                    total_rows=total_rows,
                    valid_rows=valid_rows,
                    invalid_rows=max(invalid_rows, 1 if total_rows or valid_rows else 0),
                ),
                "error_message": str(exc),
                "error_report_path": error_report_path,
                "finished_at": datetime.now(),
            },
        )
    finally:
        if should_cleanup_extract_dir and extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)


async def run_product_import(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    await ensure_tortoise_initialized()
    task = await product_import_task_controller.get(id=task_id)
    zip_path = resolve_task_zip_path(task.storage_key)
    extract_dir = get_extract_dir(task_id)

    success_count = 0
    failed_count = 0
    processed_count = 0
    canceled = False

    try:
        if (await product_import_task_controller.mark_running(task_id)).status == ProductImportTaskStatus.CANCELED:
            return

        rows, material_map = read_validation_snapshot(task_id)
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
        validation_summary = dict(task.result_summary or {})

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
            )

        error_report_path = await generate_error_report(task_id)
        result_summary = {
            **validation_summary,
            "total_count": total_rows,
            "valid_rows": total_rows,
            "invalid_rows": 0,
        }
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
            result_summary={
                **dict(task.result_summary or {}),
                "total_count": processed_count,
                "valid_rows": processed_count,
                "invalid_rows": 0,
            },
            error_message=str(exc.detail),
        )
    except Exception as exc:
        await product_import_task_controller.finish_task(
            task_id,
            success_count=success_count,
            failed_count=max(failed_count, 1),
            total_count=processed_count,
            result_summary={
                **dict(task.result_summary or {}),
                "total_count": processed_count,
                "valid_rows": processed_count,
                "invalid_rows": 0,
            },
            error_message=str(exc),
        )
    finally:
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        if zip_path and os.path.exists(zip_path):
            await cleanup_product_import_upload(zip_path)


@celery_app.task(name="product_import.validate")
def run_product_import_validation_task(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    asyncio.run(run_product_import_validation(task_id, retry_row_nos=retry_row_nos))


@celery_app.task(name="product_import.run")
def run_product_import_task(task_id: int, retry_row_nos: list[int] | None = None) -> None:
    asyncio.run(run_product_import(task_id, retry_row_nos=retry_row_nos))


@celery_app.task(name="product_import.cleanup_temp_files")
def cleanup_product_import_temp_files_task() -> dict:
    return asyncio.run(cleanup_product_import_temp_files())
