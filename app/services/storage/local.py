import asyncio
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

from app.settings import settings

from .base import (
    StorageObject,
    StorageProvider,
    UploadOptions,
    UploadResult,
    get_file_size,
    normalize_public_base_url,
    safe_join,
)


class LocalStorageProvider(StorageProvider):
    driver = "local"
    directory_mode = 0o755
    file_mode = 0o644

    def __init__(self, root_dir: str | None = None, public_base_url: str | None = None):
        self.root_dir = root_dir or settings.LOCAL_STORAGE_ROOT
        self.public_base_url = normalize_public_base_url(
            public_base_url or settings.LOCAL_STORAGE_PUBLIC_BASE_URL,
            "LOCAL_STORAGE_PUBLIC_BASE_URL",
        )

    async def upload(self, file_path: str, options: UploadOptions) -> UploadResult:
        destination = safe_join(self.root_dir, options.key)
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_directory_permissions(destination.parent)
        await asyncio.to_thread(shutil.copy2, file_path, destination)
        await asyncio.to_thread(os.chmod, destination, self.file_mode)
        return UploadResult(
            key=options.key,
            url=self.get_public_url(options.key),
            size=get_file_size(file_path),
            mime_type=options.mime_type,
            storage_driver=self.driver,
        )

    async def delete(self, key: str) -> None:
        destination = safe_join(self.root_dir, key)
        if destination.exists() and destination.is_file():
            await asyncio.to_thread(os.remove, destination)

    async def list_objects(self, prefix: str = "", batch_size: int = 1000) -> list[StorageObject]:
        prefix_path = safe_join(self.root_dir, prefix) if prefix else Path(self.root_dir).resolve()

        def collect_objects() -> list[StorageObject]:
            if not prefix_path.exists():
                return []
            objects: list[StorageObject] = []
            root_path = Path(self.root_dir).resolve()
            for file_path in prefix_path.rglob("*"):
                if not file_path.is_file():
                    continue
                stat_result = file_path.stat()
                objects.append(
                    StorageObject(
                        key=str(file_path.relative_to(root_path)).replace(os.sep, "/"),
                        last_modified=datetime.fromtimestamp(stat_result.st_mtime, tz=timezone.utc),
                        size=stat_result.st_size,
                    )
                )
            return objects

        return await asyncio.to_thread(collect_objects)

    def get_public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{str(key or '').lstrip('/')}"

    def validate_config(self) -> None:
        if not str(self.root_dir or "").strip():
            raise RuntimeError("local storage config missing: LOCAL_STORAGE_ROOT")
        if not self.public_base_url:
            raise RuntimeError("local storage config missing: LOCAL_STORAGE_PUBLIC_BASE_URL")
        safe_join(self.root_dir, "healthcheck")

    def get_public_base_url(self) -> str:
        return self.public_base_url

    def resolve_path(self, key: str) -> str:
        return str(safe_join(self.root_dir, key))

    def _ensure_directory_permissions(self, directory: Path) -> None:
        current = directory
        root_path = Path(self.root_dir).resolve()
        while True:
            os.chmod(current, self.directory_mode)
            if current == root_path or current.parent == current:
                break
            current = current.parent
