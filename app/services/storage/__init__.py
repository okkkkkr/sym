from urllib.parse import urlsplit

from .base import StorageObject, StorageProvider, UploadOptions, UploadResult
from .factory import get_storage_provider, validate_storage_provider
from .local import LocalStorageProvider


class StorageServiceAdapter:
    def __init__(self, provider: StorageProvider):
        self.provider = provider

    async def upload_file(self, local_path: str, object_key: str) -> str:
        return (
            await self.provider.upload(
                local_path,
                UploadOptions(key=str(object_key or "").lstrip("/")),
            )
        ).url

    async def delete_file(self, object_key: str) -> None:
        await self.provider.delete(str(object_key or "").lstrip("/"))

    def resolve_path(self, object_key: str) -> str:
        if hasattr(self.provider, "resolve_path"):
            return self.provider.resolve_path(object_key)
        return str(object_key or "").lstrip("/")

    def resolve_stored_path(self, stored_value: str) -> str | None:
        if not stored_value:
            return None
        normalized = str(stored_value).strip()
        if not normalized:
            return None
        if normalized.startswith(("http://", "https://")):
            normalized = urlsplit(normalized).path.lstrip("/")
        public_base_url = self.provider.get_public_base_url().rstrip("/")
        if public_base_url and normalized.startswith(public_base_url + "/"):
            normalized = normalized[len(public_base_url) + 1 :]
        else:
            base_url = public_base_url.strip("/")
            normalized = normalized.lstrip("/")
            if base_url and normalized.startswith(base_url + "/"):
                normalized = normalized[len(base_url) + 1 :]
        if hasattr(self.provider, "resolve_path"):
            return self.provider.resolve_path(normalized)
        return None


def get_storage_service() -> StorageServiceAdapter:
    return StorageServiceAdapter(get_storage_provider())


media_storage_service = get_storage_service()
artifact_storage_service = media_storage_service
storage_service = media_storage_service

__all__ = [
    "LocalStorageProvider",
    "StorageProvider",
    "StorageObject",
    "StorageServiceAdapter",
    "UploadOptions",
    "UploadResult",
    "artifact_storage_service",
    "get_storage_provider",
    "get_storage_service",
    "media_storage_service",
    "storage_service",
    "validate_storage_provider",
]
