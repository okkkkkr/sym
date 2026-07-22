import asyncio
from datetime import timezone
from uuid import uuid4

from fastapi import HTTPException

from app.log import logger
from app.settings import settings

from .base import (
    StorageObject,
    StorageProvider,
    UploadOptions,
    UploadResult,
    get_file_size,
    normalize_public_base_url,
    require_settings,
)


class R2StorageProvider(StorageProvider):
    driver = "r2"

    def __init__(self):
        self.bucket = settings.R2_BUCKET
        self.public_base_url = normalize_public_base_url(settings.R2_PUBLIC_BASE_URL, "R2_PUBLIC_BASE_URL")

    def _client(self):
        import boto3
        from botocore.config import Config

        return boto3.client(
            "s3",
            endpoint_url=settings.R2_ENDPOINT_URL,
            region_name=settings.R2_REGION or "auto",
            aws_access_key_id=settings.R2_ACCESS_KEY,
            aws_secret_access_key=settings.R2_SECRET_KEY,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path" if settings.R2_FORCE_PATH_STYLE else "auto"},
            ),
        )

    async def upload(self, file_path: str, options: UploadOptions) -> UploadResult:
        extra_args = {"ContentType": options.mime_type} if options.mime_type else {}
        try:
            await asyncio.to_thread(
                self._client().upload_file,
                file_path,
                self.bucket,
                options.key,
                ExtraArgs=extra_args,
            )
        except Exception as exc:
            error_id = uuid4().hex
            logger.exception("R2 upload failed: error_id={}, key={}", error_id, options.key)
            raise HTTPException(status_code=502, detail=f"对象存储操作失败（错误编号：{error_id}）") from exc
        return UploadResult(
            key=options.key,
            url=self.get_public_url(options.key),
            size=get_file_size(file_path),
            mime_type=options.mime_type,
            storage_driver=self.driver,
        )

    async def delete(self, key: str) -> None:
        try:
            await asyncio.to_thread(self._client().delete_object, Bucket=self.bucket, Key=str(key or "").lstrip("/"))
        except Exception as exc:
            error_id = uuid4().hex
            logger.exception("R2 delete failed: error_id={}, key={}", error_id, key)
            raise HTTPException(status_code=502, detail=f"对象存储操作失败（错误编号：{error_id}）") from exc

    async def list_objects(self, prefix: str = "", batch_size: int = 1000) -> list[StorageObject]:
        def fetch_objects():
            client = self._client()
            continuation_token = None
            objects: list[StorageObject] = []
            while True:
                params = {
                    "Bucket": self.bucket,
                    "Prefix": str(prefix or "").lstrip("/"),
                    "MaxKeys": max(1, min(int(batch_size or 1000), 1000)),
                }
                if continuation_token:
                    params["ContinuationToken"] = continuation_token
                response = client.list_objects_v2(**params)
                for item in response.get("Contents") or []:
                    last_modified = item["LastModified"]
                    if getattr(last_modified, "tzinfo", None) is None:
                        last_modified = last_modified.replace(tzinfo=timezone.utc)
                    else:
                        last_modified = last_modified.astimezone(timezone.utc)
                    objects.append(
                        StorageObject(
                            key=str(item.get("Key") or "").lstrip("/"),
                            last_modified=last_modified,
                            size=int(item.get("Size") or 0),
                        )
                    )
                if not response.get("IsTruncated"):
                    break
                continuation_token = response.get("NextContinuationToken")
                if not continuation_token:
                    break
            return objects

        try:
            return await asyncio.to_thread(fetch_objects)
        except Exception as exc:
            error_id = uuid4().hex
            logger.exception("R2 list failed: error_id={}, prefix={}", error_id, prefix)
            raise HTTPException(status_code=502, detail=f"对象存储操作失败（错误编号：{error_id}）") from exc

    def get_public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{str(key or '').lstrip('/')}"

    def validate_config(self) -> None:
        require_settings(
            {
                "R2_ENDPOINT_URL": settings.R2_ENDPOINT_URL,
                "R2_BUCKET": settings.R2_BUCKET,
                "R2_ACCESS_KEY": settings.R2_ACCESS_KEY,
                "R2_SECRET_KEY": settings.R2_SECRET_KEY,
                "R2_PUBLIC_BASE_URL": settings.R2_PUBLIC_BASE_URL,
            },
            "r2",
        )

    def get_public_base_url(self) -> str:
        return self.public_base_url
