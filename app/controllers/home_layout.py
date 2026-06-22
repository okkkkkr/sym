from copy import deepcopy
from datetime import datetime, timezone

from fastapi import HTTPException
from tortoise.transactions import in_transaction

from app.models.admin import HomeLayout, HomeLayoutItem, HomeLayoutModule
from app.schemas.home_layouts import HomeLayoutCommonConfigIn, HomeLayoutDraftSaveIn, LayoutAction
from app.services.media_cleanup import delete_media_keys, diff_removed_media_keys, normalize_media_keys
from app.services.media_storage import media_storage_service


def normalize_action(action: dict | None) -> dict:
    payload = LayoutAction(**(action or {})).model_dump()
    if not payload["text"] and not payload["link"]:
        return {}
    return payload


def normalize_common_config(common_config: dict | None) -> dict:
    return HomeLayoutCommonConfigIn(**(common_config or {})).model_dump()


def serialize_home_layout(
    layout_obj: HomeLayout | None, modules: list[dict] | None = None, published_only: bool = False
) -> dict:
    if not layout_obj:
        return {
            "page_code": "home",
            "version": 0,
            "status": "draft",
            "published_at": None,
            "updated_at": None,
            "common_config": normalize_common_config(None),
            "modules": [],
        }

    serialized_modules = []
    for module in modules or []:
        if published_only and not module["is_enabled"]:
            continue
        item_list = module["items"]
        serialized_modules.append(
            {
                "id": module["id"],
                "type": module["type"],
                "sort": module["sort"],
                "is_enabled": module["is_enabled"],
                "title": module["title"],
                "action": normalize_action(module.get("action")),
                "config": deepcopy(module.get("config") or {}),
                "items": [
                    {
                        "id": item["id"],
                        "sort": item["sort"],
                        "image": media_storage_service.serialize_object_key(item["image"]),
                        "image_key": item["image"],
                        "title": item["title"],
                        "description": item["description"],
                        "badge": item["badge"],
                        "action": normalize_action(item.get("action")),
                    }
                    for item in item_list
                ],
            }
        )
    serialized_modules.sort(key=lambda item: (item["sort"], item["id"]))
    for module in serialized_modules:
        module["items"].sort(key=lambda item: (item["sort"], item["id"]))
    return {
        "page_code": layout_obj.page_code,
        "version": layout_obj.version,
        "status": layout_obj.status,
        "published_at": layout_obj.published_at.strftime("%Y-%m-%d %H:%M:%S") if layout_obj.published_at else None,
        "updated_at": layout_obj.updated_at.strftime("%Y-%m-%d %H:%M:%S") if layout_obj.updated_at else None,
        "common_config": normalize_common_config(layout_obj.common_config),
        "modules": serialized_modules,
    }


class HomeLayoutController:
    async def get_draft(self, page_code: str = "home") -> HomeLayout:
        draft = await HomeLayout.filter(page_code=page_code, status="draft").order_by("-updated_at", "-id").first()
        if draft:
            return draft

        published = await HomeLayout.filter(page_code=page_code, status="published", is_current=True).first()
        async with in_transaction():
            draft = await HomeLayout.create(
                page_code=page_code,
                status="draft",
                version=published.version if published else 0,
                is_current=False,
                common_config=normalize_common_config(published.common_config if published else None),
            )
            if published:
                await self._clone_modules(published.id, draft.id)
        return draft

    async def get_current(self, page_code: str = "home") -> HomeLayout | None:
        return await HomeLayout.filter(page_code=page_code, status="published", is_current=True).first()

    async def get_draft_data(self, page_code: str = "home") -> dict:
        draft = await self.get_draft(page_code)
        modules = await self._serialize_modules(draft.id)
        payload = serialize_home_layout(draft, modules=modules)
        payload["has_draft_to_publish"] = await self._has_draft_to_publish(draft, modules)
        return payload

    async def get_current_data(self, page_code: str = "home") -> dict:
        current = await self.get_current(page_code)
        if not current:
            return serialize_home_layout(None)
        return serialize_home_layout(current, modules=await self._serialize_modules(current.id), published_only=True)

    async def get_current_admin_data(self, page_code: str = "home") -> dict:
        current = await self.get_current(page_code)
        if not current:
            return serialize_home_layout(None)
        return serialize_home_layout(current, modules=await self._serialize_modules(current.id))

    async def get_current_summary(self, page_code: str = "home") -> dict:
        current = await self.get_current(page_code)
        if not current:
            return {
                "page_code": page_code,
                "version": 0,
                "published_at": None,
            }
        return {
            "page_code": current.page_code,
            "version": current.version,
            "published_at": current.published_at.strftime("%Y-%m-%d %H:%M:%S") if current.published_at else None,
        }

    async def save_draft(self, payload: HomeLayoutDraftSaveIn) -> dict:
        draft = await self.get_draft(payload.page_code)
        previous_draft_keys = normalize_media_keys(await self._list_layout_image_keys(draft.id))
        published = await self.get_current(payload.page_code)
        published_keys = normalize_media_keys(await self._list_layout_image_keys(published.id)) if published else []
        current_draft_keys = normalize_media_keys(item.image for module in payload.modules for item in module.items)
        async with in_transaction():
            await HomeLayoutModule.filter(layout_id=draft.id).delete()
            draft.common_config = payload.common_config.model_dump()
            for module in payload.modules:
                module_obj = await HomeLayoutModule.create(
                    layout_id=draft.id,
                    type=module.type,
                    sort=module.sort,
                    is_enabled=module.is_enabled,
                    title=module.title,
                    action=module.action.model_dump(),
                    config=module.config,
                )
                for item in module.items:
                    await HomeLayoutItem.create(
                        module_id=module_obj.id,
                        sort=item.sort,
                        image=item.image,
                        title=item.title,
                        description=item.description,
                        badge=item.badge,
                        action=item.action.model_dump(),
                    )
            await draft.save(update_fields=["common_config", "updated_at"])
        await delete_media_keys(
            [
                item
                for item in diff_removed_media_keys(previous_draft_keys, current_draft_keys)
                if item not in set(published_keys)
            ]
        )
        return await self.get_draft_data(payload.page_code)

    async def publish(self, page_code: str = "home") -> dict:
        draft = await self.get_draft(page_code)
        modules = await self._serialize_modules(draft.id)
        current = await self.get_current(page_code)
        if current and self._build_comparable_layout(draft.common_config, modules) == self._build_comparable_layout(
            current.common_config, await self._serialize_modules(current.id)
        ):
            raise HTTPException(status_code=400, detail="当前没有可发布的变更")
        published_version = (
            await HomeLayout.filter(page_code=page_code, status="published").order_by("-version").first()
        )
        next_version = (published_version.version if published_version else 0) + 1
        published_at = datetime.now(timezone.utc)
        async with in_transaction():
            await HomeLayout.filter(page_code=page_code, status="published", is_current=True).update(is_current=False)
            published = await HomeLayout.create(
                page_code=page_code,
                status="published",
                version=next_version,
                is_current=True,
                common_config=normalize_common_config(draft.common_config),
                published_at=published_at,
            )
            await self._clone_serialized_modules(modules, published.id)
            draft.version = next_version
            await draft.save(update_fields=["version", "updated_at"])
        return await self.get_current_data(page_code)

    async def _serialize_modules(self, layout_id: int) -> list[dict]:
        modules = await HomeLayoutModule.filter(layout_id=layout_id).order_by("sort", "id")
        module_ids = [module.id for module in modules]
        items = await HomeLayoutItem.filter(module_id__in=module_ids).order_by("sort", "id") if module_ids else []
        items_by_module: dict[int, list[dict]] = {}
        for item in items:
            items_by_module.setdefault(item.module_id, []).append(
                {
                    "id": item.id,
                    "sort": item.sort,
                    "image": item.image,
                    "title": item.title,
                    "description": item.description,
                    "badge": item.badge,
                    "action": item.action or {},
                }
            )
        return [
            {
                "id": module.id,
                "type": module.type,
                "sort": module.sort,
                "is_enabled": module.is_enabled,
                "title": module.title,
                "action": module.action or {},
                "config": module.config or {},
                "items": items_by_module.get(module.id, []),
            }
            for module in modules
        ]

    async def _list_layout_image_keys(self, layout_id: int) -> list[str]:
        if not layout_id:
            return []
        return list(await HomeLayoutItem.filter(module__layout_id=layout_id).values_list("image", flat=True))

    async def _clone_modules(self, source_layout_id: int, target_layout_id: int) -> None:
        modules = await self._serialize_modules(source_layout_id)
        await self._clone_serialized_modules(modules, target_layout_id)

    async def _clone_serialized_modules(self, modules: list[dict], target_layout_id: int) -> None:
        for module in modules:
            module_obj = await HomeLayoutModule.create(
                layout_id=target_layout_id,
                type=module["type"],
                sort=module["sort"],
                is_enabled=module["is_enabled"],
                title=module["title"],
                action=module.get("action") or {},
                config=module.get("config") or {},
            )
            for item in module["items"]:
                await HomeLayoutItem.create(
                    module_id=module_obj.id,
                    sort=item["sort"],
                    image=item["image"],
                    title=item["title"],
                    description=item["description"],
                    badge=item["badge"],
                    action=item.get("action") or {},
                )

    def _build_comparable_modules(self, modules: list[dict]) -> list[dict]:
        return [
            {
                "type": module["type"],
                "sort": module["sort"],
                "is_enabled": module["is_enabled"],
                "title": module["title"].strip(),
                "action": LayoutAction(**(module.get("action") or {})).model_dump(),
                "config": deepcopy(module.get("config") or {}),
                "items": [
                    {
                        "sort": item["sort"],
                        "image": (item.get("image") or "").strip(),
                        "title": (item.get("title") or "").strip(),
                        "description": (item.get("description") or "").strip(),
                        "badge": (item.get("badge") or "").strip(),
                        "action": LayoutAction(**(item.get("action") or {})).model_dump(),
                    }
                    for item in sorted(module["items"], key=lambda item: (item["sort"], item["id"]))
                ],
            }
            for module in sorted(modules, key=lambda module: (module["sort"], module["id"]))
        ]

    def _build_comparable_layout(self, common_config: dict | None, modules: list[dict]) -> dict:
        return {
            "common_config": normalize_common_config(common_config),
            "modules": self._build_comparable_modules(modules),
        }

    async def _has_draft_to_publish(self, draft: HomeLayout, draft_modules: list[dict]) -> bool:
        current = await self.get_current(draft.page_code)
        if not current:
            return self._build_comparable_layout(draft.common_config, draft_modules) != self._build_comparable_layout(
                None, []
            )
        published_modules = await self._serialize_modules(current.id)
        return self._build_comparable_layout(draft.common_config, draft_modules) != self._build_comparable_layout(
            current.common_config, published_modules
        )


home_layout_controller = HomeLayoutController()
