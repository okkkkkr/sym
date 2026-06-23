from fastapi import HTTPException

from app.controllers.product_video_update_plan import (
    product_video_update_plan_controller,
)
from app.controllers.video_resource import video_resource_controller
from app.log import logger
from app.models.admin import Product, User
from app.models.enums import ProductVideoUpdatePlanStatus, VideoResourceStatus
from app.services.media_cleanup import delete_media_keys, diff_removed_media_keys
from app.services.media_storage import media_storage_service


class ProductVideoUpdateService:
    @staticmethod
    def normalize_video_key(value: str | None) -> str:
        normalized_key = media_storage_service.normalize_key(str(value or "").strip())
        if normalized_key.startswith(("http://", "https://")):
            return ""
        return normalized_key

    def normalize_video_keys(self, values: list[str] | tuple[str, ...]) -> list[str]:
        normalized_keys: list[str] = []
        for value in values:
            normalized_key = self.normalize_video_key(value)
            if normalized_key and normalized_key not in normalized_keys:
                normalized_keys.append(normalized_key)
        return normalized_keys

    async def extract_video_submission(
        self,
        *,
        video_items: list[dict] | None,
        legacy_video_keys: list[str],
        current_user: User,
        product_id: int | None = None,
    ) -> tuple[list[dict], list[str], list[int]]:
        if not video_items:
            normalized_keys = self.normalize_video_keys(legacy_video_keys or [])
            return [{"type": "key", "value": key} for key in normalized_keys], normalized_keys, []

        normalized_items: list[dict] = []
        direct_keys: list[str] = []
        resource_ids: list[int] = []
        seen_pairs: set[tuple[str, str | int]] = set()

        for item in video_items:
            item_type = str(item.get("type") or "").strip().lower()
            raw_value = item.get("value")
            if item_type == "key":
                normalized_key = self.normalize_video_key(str(raw_value or "").strip())
                if not normalized_key:
                    continue
                dedupe_key = (item_type, normalized_key)
                if dedupe_key in seen_pairs:
                    continue
                seen_pairs.add(dedupe_key)
                direct_keys.append(normalized_key)
                normalized_items.append({"type": "key", "value": normalized_key})
                continue
            if item_type == "resource":
                try:
                    resource_id = int(raw_value)
                except (TypeError, ValueError) as exc:
                    raise HTTPException(status_code=400, detail="video_items resource value invalid") from exc
                dedupe_key = (item_type, resource_id)
                if dedupe_key in seen_pairs:
                    continue
                seen_pairs.add(dedupe_key)
                resource_ids.append(resource_id)
                normalized_items.append({"type": "resource", "value": resource_id})
                continue
            raise HTTPException(status_code=400, detail="video_items type invalid")

        resource_map = {
            resource.id: resource
            for resource in await video_resource_controller.model.filter(id__in=resource_ids).all()
        }
        if len(resource_map) != len(resource_ids):
            raise HTTPException(status_code=400, detail="video resource not found")
        for resource_id in resource_ids:
            resource = resource_map[resource_id]
            if not current_user.is_superuser and resource.created_by != current_user.id:
                raise HTTPException(status_code=403, detail="当前用户无权使用该视频资源")
            if resource.status == VideoResourceStatus.FAILED:
                raise HTTPException(status_code=400, detail="存在处理失败的视频资源，请重新上传")
            if resource.product_id and resource.product_id != product_id:
                raise HTTPException(status_code=400, detail="视频资源已被其他商品占用")

        return normalized_items, direct_keys, resource_ids

    async def replace_active_plan(
        self,
        *,
        product: Product,
        items: list[dict],
        previous_video_keys: list[str],
        current_user: User,
        resource_ids: list[int],
    ) -> tuple[object, bool]:
        await product_video_update_plan_controller.model.filter(
            product_id=product.id,
            status=ProductVideoUpdatePlanStatus.ACTIVE,
        ).update(status=ProductVideoUpdatePlanStatus.SUPERSEDED)
        plan = await product_video_update_plan_controller.create(
            obj_in={
                "product_id": product.id,
                "status": ProductVideoUpdatePlanStatus.ACTIVE,
                "items": items,
                "previous_video_keys": previous_video_keys,
                "created_by": current_user.id,
            }
        )
        if resource_ids:
            await video_resource_controller.model.filter(id__in=resource_ids).update(
                product_id=product.id,
                update_plan_id=plan.id,
            )
        applied = await self.try_apply_plan(plan.id)
        return plan, applied

    async def try_apply_plan(self, plan_id: int) -> bool:
        plan = await product_video_update_plan_controller.model.get_or_none(id=plan_id)
        if not plan or plan.status != ProductVideoUpdatePlanStatus.ACTIVE:
            return False

        product = await Product.get_or_none(id=plan.product_id)
        if not product:
            await product_video_update_plan_controller.update(
                id=plan.id,
                obj_in={
                    "status": ProductVideoUpdatePlanStatus.FAILED,
                    "error_message": "关联好物不存在",
                },
            )
            return False

        resource_ids = [int(item["value"]) for item in plan.items if item.get("type") == "resource"]
        resources = {
            resource.id: resource
            for resource in await video_resource_controller.model.filter(id__in=resource_ids).all()
        }
        if len(resources) != len(resource_ids):
            await product_video_update_plan_controller.update(
                id=plan.id,
                obj_in={
                    "status": ProductVideoUpdatePlanStatus.FAILED,
                    "error_message": "视频资源缺失",
                },
            )
            return False

        if any(resource.status == VideoResourceStatus.FAILED for resource in resources.values()):
            await product_video_update_plan_controller.update(
                id=plan.id,
                obj_in={
                    "status": ProductVideoUpdatePlanStatus.FAILED,
                    "error_message": "存在处理失败的视频资源",
                },
            )
            return False

        if any(resource.status != VideoResourceStatus.UPLOADED for resource in resources.values()):
            return False

        final_video_keys: list[str] = []
        for item in plan.items:
            if item.get("type") == "key":
                normalized_key = self.normalize_video_key(str(item.get("value") or "").strip())
            else:
                normalized_key = self.normalize_video_key(resources[int(item["value"])].storage_key)
            if normalized_key and normalized_key not in final_video_keys:
                final_video_keys.append(normalized_key)

        previous_video_keys = self.normalize_video_keys(plan.previous_video_keys or [])
        product.update_from_dict({"video_keys": final_video_keys})
        await product.save()
        await product_video_update_plan_controller.update(
            id=plan.id,
            obj_in={
                "status": ProductVideoUpdatePlanStatus.APPLIED,
                "error_message": None,
            },
        )
        await delete_media_keys(diff_removed_media_keys(previous_video_keys, final_video_keys))
        logger.info("applied product video update plan: product_id={}, plan_id={}", product.id, plan.id)
        return True

    async def mark_plan_failed(self, plan_id: int, error_message: str) -> None:
        plan = await product_video_update_plan_controller.model.get_or_none(id=plan_id)
        if not plan or plan.status != ProductVideoUpdatePlanStatus.ACTIVE:
            return
        await product_video_update_plan_controller.update(
            id=plan.id,
            obj_in={
                "status": ProductVideoUpdatePlanStatus.FAILED,
                "error_message": str(error_message or "").strip() or "视频处理失败",
            },
        )


product_video_update_service = ProductVideoUpdateService()
