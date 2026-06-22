import asyncio
from datetime import datetime, timezone

from fastapi import HTTPException

from app.settings import settings

from .base import (
    StorageProvider,
    StorageObject,
    UploadOptions,
    UploadResult,
    get_file_size,
    normalize_public_base_url,
    require_settings,
)


class QiniuProvider(StorageProvider):
    driver = "qiniu"

    def __init__(self):
        self.bucket = settings.QINIU_BUCKET
        self.public_base_url = normalize_public_base_url(
            settings.QINIU_PUBLIC_BASE_URL or self._legacy_public_base_url(),
            "QINIU_PUBLIC_BASE_URL",
        )

    @staticmethod
    def _legacy_public_base_url() -> str:
        domain = str(settings.QINIU_DOMAIN or "").strip()
        if not domain:
            return ""
        if domain.startswith(("http://", "https://")):
            return domain.rstrip("/")
        return f"{str(settings.QINIU_DOMAIN_SCHEME or 'https').strip() or 'https'}://{domain.lstrip('/')}".rstrip("/")

    @staticmethod
    def _auth():
        from qiniu import Auth

        return Auth(settings.QINIU_ACCESS_KEY, settings.QINIU_SECRET_KEY)

    async def upload(self, file_path: str, options: UploadOptions) -> UploadResult:
        def upload_file():
            from qiniu import put_file

            token = self._auth().upload_token(self.bucket, options.key)
            return put_file(token, options.key, file_path, mime_type=options.mime_type or None)

        try:
            _, info = await asyncio.to_thread(upload_file)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"七牛上传失败: {exc}") from exc
        if getattr(info, "status_code", 0) != 200:
            raise HTTPException(
                status_code=502, detail=f"七牛上传失败({getattr(info, 'status_code', 'unknown')}): {info}"
            )
        return UploadResult(
            key=options.key,
            url=self.get_public_url(options.key),
            size=get_file_size(file_path),
            mime_type=options.mime_type,
            storage_driver=self.driver,
        )

    async def delete(self, key: str) -> None:
        def delete_file():
            from qiniu import BucketManager

            return BucketManager(self._auth()).delete(self.bucket, str(key or "").lstrip("/"))

        try:
            _, info = await asyncio.to_thread(delete_file)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"七牛删除失败: {exc}") from exc
        if getattr(info, "status_code", 0) not in {200, 612}:
            raise HTTPException(
                status_code=502, detail=f"七牛删除失败({getattr(info, 'status_code', 'unknown')}): {info}"
            )

    async def list_objects(self, prefix: str = "", batch_size: int = 1000) -> list[StorageObject]:
        def fetch_objects():
            from qiniu import BucketManager

            bucket_manager = BucketManager(self._auth())
            marker = None
            objects: list[StorageObject] = []
            limit = max(1, min(int(batch_size or 1000), 1000))
            normalized_prefix = str(prefix or "").lstrip("/") or None

            while True:
                ret, eof, info = bucket_manager.list(self.bucket, normalized_prefix, marker, limit, None)
                if getattr(info, "status_code", 0) != 200:
                    raise RuntimeError(f"七牛列举对象失败({getattr(info, 'status_code', 'unknown')}): {info}")
                for item in (ret or {}).get("items") or []:
                    put_time = int(item.get("putTime") or 0)
                    last_modified = (
                        datetime.fromtimestamp(put_time / 10000000, tz=timezone.utc)
                        if put_time
                        else datetime.fromtimestamp(0, tz=timezone.utc)
                    )
                    objects.append(
                        StorageObject(
                            key=str(item.get("key") or "").lstrip("/"),
                            last_modified=last_modified,
                            size=int(item.get("fsize") or 0),
                        )
                    )
                if eof:
                    break
                marker = (ret or {}).get("marker")
                if not marker:
                    break
            return objects

        try:
            return await asyncio.to_thread(fetch_objects)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"七牛列举对象失败: {exc}") from exc

    def get_public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{str(key or '').lstrip('/')}"

    def validate_config(self) -> None:
        require_settings(
            {
                "QINIU_ACCESS_KEY": settings.QINIU_ACCESS_KEY,
                "QINIU_SECRET_KEY": settings.QINIU_SECRET_KEY,
                "QINIU_BUCKET": settings.QINIU_BUCKET,
                "QINIU_REGION": settings.QINIU_REGION,
                "QINIU_PUBLIC_BASE_URL": self.public_base_url,
            },
            "qiniu",
        )

    def get_public_base_url(self) -> str:
        return self.public_base_url
