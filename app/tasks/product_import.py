import asyncio
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException
from tortoise import Tortoise

from app.controllers.product import product_controller
from app.controllers.product_import import product_import_task_controller, product_import_task_item_controller
from app.core.celery_app import celery_app
from app.models.enums import ProductImportTaskItemStatus, ProductImportTaskStatus
from app.services import product_import_parser_service, product_import_zip_service, storage_service
from app.settings import settings
from app.utils.excel_export import build_xlsx_content


async def ensure_tortoise_initialized() -> None:
    if not Tortoise._inited:
        await Tortoise.init(config=settings.TORTOISE_ORM)


def build_media_object_key(product_name: str, local_path: str) -> str:
    filename = Path(local_path).name
    return f"products/{product_name}/{filename}"


async def upload_media_files(product_name: str, file_paths: list[str]) -> list[str]:
    urls: list[str] = []
    for file_path in file_paths:
        urls.append(await storage_service.upload_file(file_path, build_media_object_key(product_name, file_path)))
    return urls


async def generate_error_report(task_id: int) -> str | None:
    items = await product_import_task_item_controller.model.filter(task_id=task_id).order_by("row_no", "id")
    error_rows = []
    for item in items:
        if item.status == ProductImportTaskItemStatus.SUCCESS:
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
        return await storage_service.upload_file(temp_path, f"product-import/error-report/{task_id}.xlsx")
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


async def run_product_import(task_id: int) -> None:
    await ensure_tortoise_initialized()
    task = await product_import_task_controller.get(id=task_id)
    zip_path = task.storage_key
    if not os.path.isabs(zip_path):
        zip_path = os.path.join(settings.BASE_DIR, zip_path)

    extract_dir = ""
    success_count = 0
    failed_count = 0
    processed_count = 0
    canceled = False

    try:
        await product_import_task_controller.mark_running(task_id)

        product_import_zip_service.validate_zip(zip_path)
        extract_dir = product_import_zip_service.extract_to_temp(zip_path, task_id)
        workbook_path = os.path.join(extract_dir, "product.xlsx")
        material_map = product_import_zip_service.scan_materials(extract_dir)
        parse_result = await product_import_parser_service.parse(workbook_path)

        await product_import_task_controller.update_progress(
            task_id,
            total_count=parse_result.total_rows,
            processed_count=0,
            success_count=0,
            failed_count=0,
            status=ProductImportTaskStatus.RUNNING,
        )

        for row in parse_result.rows:
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
                row_errors.append("material directory not found")
            else:
                if not material_set.images:
                    row_errors.append("material directory must contain at least one image")
                if not material_set.cover_image:
                    row_errors.append("cover image could not be resolved")

            if row_errors:
                failed_count += 1
                processed_count += 1
                await product_import_task_item_controller.mark_failed(item.id, message="; ".join(row_errors))
                await product_import_task_controller.update_progress(
                    task_id,
                    total_count=parse_result.total_rows,
                    processed_count=processed_count,
                    success_count=success_count,
                    failed_count=failed_count,
                    status=ProductImportTaskStatus.RUNNING,
                )
                continue

            try:
                image_urls = await upload_media_files(row.name, material_set.images)
                video_urls = await upload_media_files(row.name, material_set.videos)
                cover_image_url = next((url for url in image_urls if Path(url).name == Path(material_set.cover_image).name), None)
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
                payload["product_code"] = await product_controller.build_product_code(row.product_code_custom)
                product = await product_controller.create_with_tags(obj_in=payload, tag_ids=row.tag_ids)

                success_count += 1
                processed_count += 1
                success_message = "created successfully"
                if row.duplicate_hint:
                    success_message = f"{success_message}; duplicate product name detected"
                await product_import_task_item_controller.mark_success(
                    item.id,
                    message=success_message,
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
                total_count=parse_result.total_rows,
                processed_count=processed_count,
                success_count=success_count,
                failed_count=failed_count,
                status=ProductImportTaskStatus.RUNNING,
            )

        error_report_path = await generate_error_report(task_id)
        if canceled:
            await product_import_task_controller.update(
                id=task_id,
                obj_in={
                    "status": ProductImportTaskStatus.CANCELED,
                    "processed_count": processed_count,
                    "success_count": success_count,
                    "failed_count": failed_count,
                    "progress": 0
                    if not parse_result.total_rows
                    else min(100, int((processed_count / parse_result.total_rows) * 100)),
                    "result_summary": {
                        "total_count": parse_result.total_rows,
                        "valid_rows": parse_result.valid_rows,
                        "invalid_rows": parse_result.invalid_rows,
                    },
                    "error_report_path": error_report_path,
                    "finished_at": datetime.now(),
                },
            )
        else:
            await product_import_task_controller.finish_task(
                task_id,
                success_count=success_count,
                failed_count=failed_count,
                total_count=parse_result.total_rows,
                result_summary={
                    "total_count": parse_result.total_rows,
                    "valid_rows": parse_result.valid_rows,
                    "invalid_rows": parse_result.invalid_rows,
                },
                error_report_path=error_report_path,
            )
    except HTTPException as exc:
        await product_import_task_controller.finish_task(
            task_id,
            success_count=success_count,
            failed_count=max(failed_count, 1),
            total_count=processed_count,
            result_summary={"total_count": processed_count},
            error_message=str(exc.detail),
        )
    except Exception as exc:
        await product_import_task_controller.finish_task(
            task_id,
            success_count=success_count,
            failed_count=max(failed_count, 1),
            total_count=processed_count,
            result_summary={"total_count": processed_count},
            error_message=str(exc),
        )
    finally:
        if extract_dir and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)


@celery_app.task(name="product_import.run")
def run_product_import_task(task_id: int) -> None:
    asyncio.run(run_product_import(task_id))