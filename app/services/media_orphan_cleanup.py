from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from app.log import logger
from app.models.admin import Contact, HomeLayoutItem, Product, SiteConfig
from app.services.media_cleanup import normalize_media_key, normalize_media_keys
from app.services.storage import get_storage_provider
from app.settings import settings


@dataclass(frozen=True)
class OrphanMediaCleanupStats:
    enabled: bool
    dry_run: bool
    referenced_keys: int
    scanned_objects: int
    retained_objects: int
    orphan_objects: int
    deleted_objects: int
    deleted_bytes: int
    failures: list[dict]

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "dry_run": self.dry_run,
            "referenced_keys": self.referenced_keys,
            "scanned_objects": self.scanned_objects,
            "retained_objects": self.retained_objects,
            "orphan_objects": self.orphan_objects,
            "deleted_objects": self.deleted_objects,
            "deleted_bytes": self.deleted_bytes,
            "failures": self.failures,
        }


class MediaOrphanCleanupService:
    async def collect_referenced_keys(self) -> set[str]:
        referenced_keys = set()
        referenced_keys.update(
            normalize_media_keys(await SiteConfig.all().exclude(logo_key="").values_list("logo_key", flat=True))
        )
        referenced_keys.update(
            normalize_media_keys(
                await Contact.filter(is_deleted=False).exclude(qr_image_url="").values_list("qr_image_url", flat=True)
            )
        )
        referenced_keys.update(
            normalize_media_keys(await HomeLayoutItem.exclude(image="").values_list("image", flat=True))
        )
        product_media_keys = await Product.all().values("cover_image_key", "image_keys", "video_keys")
        referenced_keys.update(
            normalize_media_keys(
                key
                for item in product_media_keys
                for key in [
                    item.get("cover_image_key"),
                    *(item.get("image_keys") or []),
                    *(item.get("video_keys") or []),
                ]
            )
        )
        return referenced_keys

    async def cleanup_orphan_files(self) -> dict:
        stats = {
            "enabled": settings.MEDIA_ORPHAN_CLEANUP_ENABLED,
            "dry_run": settings.MEDIA_ORPHAN_CLEANUP_DRY_RUN,
            "referenced_keys": 0,
            "scanned_objects": 0,
            "retained_objects": 0,
            "orphan_objects": 0,
            "deleted_objects": 0,
            "deleted_bytes": 0,
            "failures": [],
        }
        if not settings.MEDIA_ORPHAN_CLEANUP_ENABLED:
            return stats

        provider = get_storage_provider()
        referenced_keys = await self.collect_referenced_keys()
        retention_deadline = datetime.now(timezone.utc) - timedelta(
            hours=max(1, int(settings.MEDIA_ORPHAN_RETENTION_HOURS))
        )
        prefixes = self._normalize_prefixes(settings.MEDIA_ORPHAN_CLEANUP_PREFIXES)
        batch_size = max(1, int(settings.MEDIA_ORPHAN_CLEANUP_BATCH_SIZE))

        stats["referenced_keys"] = len(referenced_keys)
        dry_run = bool(settings.MEDIA_ORPHAN_CLEANUP_DRY_RUN)

        for prefix in prefixes:
            objects = await provider.list_objects(prefix=prefix, batch_size=batch_size)
            for storage_object in objects:
                normalized_key = normalize_media_key(storage_object.key)
                if not normalized_key:
                    continue
                stats["scanned_objects"] += 1
                if normalized_key in referenced_keys:
                    stats["retained_objects"] += 1
                    continue
                if storage_object.last_modified > retention_deadline:
                    stats["retained_objects"] += 1
                    continue
                stats["orphan_objects"] += 1
                if dry_run:
                    logger.info(
                        "dry-run orphan media candidate: driver={}, key={}, size={}",
                        provider.driver,
                        normalized_key,
                        storage_object.size,
                    )
                    continue
                try:
                    await provider.delete(normalized_key)
                    stats["deleted_objects"] += 1
                    stats["deleted_bytes"] += storage_object.size
                except Exception as exc:
                    logger.exception("删除孤儿媒体失败: {}", normalized_key)
                    stats["failures"].append({"key": normalized_key, "error": str(exc)})

        logger.info(
            "orphan media cleanup finished: driver={}, dry_run={}, scanned={}, orphan={}, deleted={}",
            provider.driver,
            dry_run,
            stats["scanned_objects"],
            stats["orphan_objects"],
            stats["deleted_objects"],
        )
        return stats

    @staticmethod
    def _normalize_prefixes(prefixes: Iterable[str]) -> list[str]:
        return [str(prefix or "").strip().lstrip("/") for prefix in prefixes if str(prefix or "").strip()]


media_orphan_cleanup_service = MediaOrphanCleanupService()
