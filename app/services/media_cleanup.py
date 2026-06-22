from collections.abc import Iterable

from app.log import logger
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


async def delete_media_keys(values: Iterable[str | None]) -> list[str]:
    deleted_keys = []
    for key in normalize_media_keys(values):
        try:
            await media_storage_service.delete(key)
            deleted_keys.append(key)
        except Exception:
            logger.exception("删除媒体资源失败: {}", key)
    return deleted_keys
