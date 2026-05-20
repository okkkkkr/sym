import os
import shutil
from abc import ABC, abstractmethod

from app.settings import settings


class StorageService(ABC):
    @abstractmethod
    async def upload_file(self, local_path: str, object_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def delete_file(self, object_key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def resolve_path(self, object_key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def resolve_stored_path(self, stored_value: str) -> str | None:
        raise NotImplementedError


class LocalStorageService(StorageService):
    def __init__(self, root_dir: str | None = None, base_url: str = "/uploads"):
        self.root_dir = root_dir or os.path.join(settings.BASE_DIR, "uploads")
        self.base_url = base_url.rstrip("/")

    async def upload_file(self, local_path: str, object_key: str) -> str:
        destination = self.resolve_path(object_key)
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copy2(local_path, destination)
        return f"{self.base_url}/{object_key.lstrip('/')}"

    async def delete_file(self, object_key: str) -> None:
        destination = self.resolve_path(object_key)
        if os.path.exists(destination):
            os.remove(destination)

    def resolve_path(self, object_key: str) -> str:
        normalized_key = object_key.lstrip("/")
        return os.path.join(self.root_dir, normalized_key)

    def resolve_stored_path(self, stored_value: str) -> str | None:
        if not stored_value:
            return None
        normalized = str(stored_value).strip()
        if normalized.startswith(self.base_url + "/"):
            object_key = normalized[len(self.base_url) + 1 :]
            return self.resolve_path(object_key)
        if os.path.isabs(normalized):
            return normalized
        return None


class QiniuStorageService(StorageService):
    async def upload_file(self, local_path: str, object_key: str) -> str:
        raise NotImplementedError("Qiniu storage service is not implemented yet")

    async def delete_file(self, object_key: str) -> None:
        raise NotImplementedError("Qiniu storage service is not implemented yet")

    def resolve_path(self, object_key: str) -> str:
        return object_key

    def resolve_stored_path(self, stored_value: str) -> str | None:
        return None


def get_storage_service() -> StorageService:
    provider = str(settings.STORAGE_PROVIDER).strip().lower()
    if provider == "qiniu":
        return QiniuStorageService()
    return LocalStorageService()


storage_service = get_storage_service()