from collections.abc import Iterable

from app.log import logger
from app.models.admin import Contact, HomeLayoutItem, MediaUpload, Product, SiteConfig
from app.services.media_storage import media_storage_service


def normalize_media_key(value: str | None) -> str:
    normalized_value = str(value or "").strip()
    if not normalized_value:
        return ""
    return media_storage_service.normalize_key(normalized_value)


def normalize_media_keys(values: Iterable[str | None]) -> list[str]:
    return list(dict.fromkeys(item for item in (normalize_media_key(value) for value in values) if item))


def diff_removed_media_keys(previous_values: Iterable[str | None], current_values: Iterable[str | None]) -> list[str]:
    current_keys = set(normalize_media_keys(current_values))
    return [item for item in normalize_media_keys(previous_values) if item not in current_keys]


async def collect_referenced_media_keys() -> set[str]:
    referenced_keys = set()
    referenced_keys.update(
        normalize_media_keys(await SiteConfig.all().exclude(logo_key="").values_list("logo_key", flat=True))
    )
    referenced_keys.update(
        normalize_media_keys(
            await Contact.filter(is_deleted=False).exclude(qr_image_url="").values_list("qr_image_url", flat=True)
        )
    )
    referenced_keys.update(normalize_media_keys(await HomeLayoutItem.exclude(image="").values_list("image", flat=True)))
    referenced_keys.update(
        normalize_media_keys(
            key
            for item in await Product.all().values("cover_image_key", "image_keys", "video_keys")
            for key in [
                item.get("cover_image_key"),
                *(item.get("image_keys") or []),
                *(item.get("video_keys") or []),
            ]
        )
    )
    return referenced_keys


async def delete_media_keys(values: Iterable[str | None]) -> list[str]:
    deleted_keys = []
    for key in normalize_media_keys(values):
        try:
            await media_storage_service.delete(key)
            await MediaUpload.filter(object_key=key).delete()
            deleted_keys.append(key)
        except Exception:
            logger.exception("删除媒体资源失败: {}", key)
    return deleted_keys


async def delete_owned_transient_media_keys(values: Iterable[str | None], user_id: int) -> list[str]:
    requested_keys = normalize_media_keys(values)
    if not requested_keys:
        return []
    owned_keys = set(
        await MediaUpload.filter(object_key__in=requested_keys, uploaded_by=user_id).values_list("object_key", flat=True)
    )
    referenced_keys = await collect_referenced_media_keys()
    return await delete_media_keys(key for key in requested_keys if key in owned_keys and key not in referenced_keys)
