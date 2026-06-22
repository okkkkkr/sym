import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException


@dataclass(frozen=True)
class UploadOptions:
    key: str
    file_name: str = ""
    mime_type: str = ""


@dataclass(frozen=True)
class UploadResult:
    key: str
    url: str
    size: int
    mime_type: str
    storage_driver: str

    def to_api_dict(self) -> dict:
        return {
            "key": self.key,
            "url": self.url,
            "size": self.size,
            "mimeType": self.mime_type,
            "storageDriver": self.storage_driver,
        }


@dataclass(frozen=True)
class StorageObject:
    key: str
    last_modified: datetime
    size: int


class StorageProvider(ABC):
    driver: str

    @abstractmethod
    async def upload(self, file_path: str, options: UploadOptions) -> UploadResult:
        raise NotImplementedError

    @abstractmethod
    async def delete(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_public_url(self, key: str) -> str:
        raise NotImplementedError

    @abstractmethod
    def validate_config(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_objects(self, prefix: str = "", batch_size: int = 1000) -> list[StorageObject]:
        raise NotImplementedError

    def normalize_key(self, value: str | None) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            return ""
        if not normalized.startswith(("http://", "https://")):
            return normalized.lstrip("/")

        public_base_url = self.get_public_base_url()
        if not public_base_url:
            return normalized

        parsed_value = urlsplit(normalized)
        parsed_base = urlsplit(public_base_url)
        if parsed_value.netloc != parsed_base.netloc:
            return normalized

        base_path = parsed_base.path.strip("/")
        value_path = parsed_value.path.strip("/")
        if base_path and value_path.startswith(base_path + "/"):
            return value_path[len(base_path) + 1 :].split("?", 1)[0]
        if not base_path:
            return value_path.split("?", 1)[0]
        return normalized

    def get_public_base_url(self) -> str:
        return ""


def require_settings(settings_map: dict[str, object], driver: str) -> None:
    missing_names = [name for name, value in settings_map.items() if not str(value or "").strip()]
    if missing_names:
        raise RuntimeError(f"{driver} storage config missing: {', '.join(missing_names)}")


def get_file_size(file_path: str) -> int:
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="待上传文件不存在")
    return os.path.getsize(file_path)


def normalize_public_base_url(value: str, setting_name: str) -> str:
    normalized = str(value or "").strip().rstrip("/")
    if not normalized:
        return ""
    if normalized.startswith("/"):
        return normalized
    if normalized.startswith(("http://", "https://")):
        return normalized
    raise RuntimeError(f"{setting_name} must be an absolute http(s) URL or an absolute path")


def safe_join(root_dir: str, key: str) -> Path:
    root_path = Path(root_dir).resolve()
    resolved_path = (root_path / str(key or "").lstrip("/")).resolve()
    try:
        resolved_path.relative_to(root_path)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="文件 Key 不合法") from exc
    return resolved_path
