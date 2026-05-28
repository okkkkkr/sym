import os
import shutil
from abc import ABC, abstractmethod
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException

from app.services.product_media_upload import _urlsafe_base64, product_media_upload_service
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
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="待上传文件不存在")

        product_media_upload_service._validate_settings()
        upload_token = product_media_upload_service._build_upload_token(object_key)
        upload_url = product_media_upload_service._normalize_upload_host()
        try:
            with open(local_path, "rb") as file_obj:
                async with httpx.AsyncClient(timeout=None) as client:
                    response = await client.post(
                        upload_url,
                        data={"token": upload_token, "key": object_key},
                        files={"file": (os.path.basename(local_path), file_obj)},
                    )
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise HTTPException(status_code=502, detail=self._format_qiniu_error(exc.response)) from exc
        except httpx.HTTPError as exc:
            raise HTTPException(status_code=502, detail=f"七牛上传请求失败: {exc}") from exc

        return product_media_upload_service.build_public_url(object_key)

    async def delete_file(self, object_key: str) -> None:
        product_media_upload_service._validate_settings()
        entry_uri = _urlsafe_base64(f"{settings.QINIU_BUCKET}:{self._extract_object_key(object_key)}".encode())
        path = f"/delete/{entry_uri}"
        host = "rs.qiniu.com"
        token = self._build_management_token("POST", path, host)
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"http://{host}{path}",
                headers={"Authorization": f"Qiniu {token}"},
            )
        if response.status_code not in {200, 612}:
            raise HTTPException(status_code=502, detail=self._format_qiniu_error(response))

    def resolve_path(self, object_key: str) -> str:
        return object_key

    def resolve_stored_path(self, stored_value: str) -> str | None:
        return None

    @staticmethod
    def _extract_object_key(stored_value: str) -> str:
        object_key = product_media_upload_service.extract_object_key(stored_value)
        if object_key:
            return object_key
        parsed = urlparse(str(stored_value or ""))
        if parsed.scheme and parsed.netloc:
            return parsed.path.lstrip("/")
        return str(stored_value or "").lstrip("/")

    @staticmethod
    def _build_management_token(method: str, path_with_query: str, host: str) -> str:
        signing_data = f"{method} {path_with_query}\nHost: {host}\n\n"
        digest = product_media_upload_service._sign_download_path(signing_data)
        return f"{settings.QINIU_ACCESS_KEY}:{digest}"

    @staticmethod
    def _format_qiniu_error(response: httpx.Response) -> str:
        try:
            data = response.json()
            message = data.get("error") or data.get("message")
        except ValueError:
            message = response.text
        return f"七牛请求失败({response.status_code}): {message or '未知错误'}"


def get_storage_service() -> StorageService:
    provider = str(settings.STORAGE_PROVIDER).strip().lower()
    if provider == "qiniu":
        return QiniuStorageService()
    return LocalStorageService()


artifact_storage_service = LocalStorageService()
media_storage_service = get_storage_service()
storage_service = media_storage_service
