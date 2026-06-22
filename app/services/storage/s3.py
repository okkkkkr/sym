import asyncio
from datetime import timezone

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


class S3StorageProvider(StorageProvider):
    driver = "s3"

    def __init__(self):
        self.bucket = settings.S3_BUCKET
        self.public_base_url = normalize_public_base_url(settings.S3_PUBLIC_BASE_URL, "S3_PUBLIC_BASE_URL")

    def _client(self):
        import boto3
        from botocore.config import Config

        client_config = Config(
            s3={"addressing_style": "path" if settings.S3_FORCE_PATH_STYLE else "auto"},
        )
        return boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            region_name=settings.S3_REGION or None,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=client_config,
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
            raise HTTPException(status_code=502, detail=f"S3 上传失败: {exc}") from exc
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
            raise HTTPException(status_code=502, detail=f"S3 删除失败: {exc}") from exc

    async def list_objects(self, prefix: str = "", batch_size: int = 1000) -> list[StorageObject]:
        def fetch_objects():
            client = self._client()
            continuation_token = None
            objects: list[StorageObject] = []
            while True:
                params = {
                    "Bucket": self.bucket,
                    "Prefix": str(prefix or "").lstrip("/"),
                    "MaxKeys": max(1, int(batch_size or 1000)),
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
            raise HTTPException(status_code=502, detail=f"S3 列举对象失败: {exc}") from exc

    def get_public_url(self, key: str) -> str:
        return f"{self.public_base_url}/{str(key or '').lstrip('/')}"

    def validate_config(self) -> None:
        require_settings(
            {
                "S3_BUCKET": settings.S3_BUCKET,
                "S3_REGION": settings.S3_REGION,
                "S3_ACCESS_KEY": settings.S3_ACCESS_KEY,
                "S3_SECRET_KEY": settings.S3_SECRET_KEY,
                "S3_PUBLIC_BASE_URL": settings.S3_PUBLIC_BASE_URL,
            },
            "s3",
        )

    def get_public_base_url(self) -> str:
        return self.public_base_url
