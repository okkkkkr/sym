import mimetypes
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import HTTPException, UploadFile

from app.log import logger
from app.services.product_media_upload import PRODUCT_MEDIA_TYPE_RULES, ProductMediaUploadService
from app.services.storage import UploadOptions, get_storage_provider
from app.settings import settings


class MediaStorageService:
    chunk_size = 1024 * 1024

    def __init__(self):
        self.key_builder = ProductMediaUploadService

    def validate_provider_config(self) -> None:
        get_storage_provider().validate_config()

    def validate_media_type(self, media_type: str) -> dict:
        media_rule = PRODUCT_MEDIA_TYPE_RULES.get(str(media_type or "").strip().lower())
        if not media_rule:
            raise HTTPException(status_code=400, detail="不支持的媒体类型")
        return media_rule

    def sanitize_filename(self, file_name: str) -> str:
        return self.key_builder._sanitize_filename(file_name)

    def validate_file(self, file_name: str, content_type: str | None, media_rule: dict) -> str:
        self.key_builder._validate_file(file_name, content_type, media_rule)
        return str(content_type or "").strip().lower() or mimetypes.guess_type(file_name)[0] or ""

    def build_object_key(self, media_type: str, file_name: str) -> str:
        self.validate_media_type(media_type)
        return self.key_builder._build_object_key(media_type, file_name)

    async def upload(self, upload_file: UploadFile, media_type: str) -> dict:
        if not upload_file:
            raise HTTPException(status_code=400, detail="未找到待上传文件")
        media_rule = self.validate_media_type(media_type)
        file_name = self.sanitize_filename(upload_file.filename or "file")
        mime_type = self.validate_file(file_name, upload_file.content_type, media_rule)
        object_key = self.build_object_key(str(media_type or "").strip().lower(), file_name)
        return (await self.upload_file(upload_file, object_key, mime_type=mime_type)).to_api_dict()

    async def upload_file(self, upload_file: UploadFile, object_key: str, mime_type: str = ""):
        temp_path = await self._save_upload_file(upload_file)
        try:
            return await self.upload_local_file(
                temp_path,
                object_key,
                file_name=upload_file.filename or Path(object_key).name,
                mime_type=mime_type or upload_file.content_type or mimetypes.guess_type(object_key)[0] or "",
            )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    async def upload_local_file(self, local_path: str, object_key: str, file_name: str = "", mime_type: str = ""):
        if not os.path.exists(local_path):
            raise HTTPException(status_code=404, detail="待上传文件不存在")
        self._validate_size(os.path.getsize(local_path))
        key = str(object_key or "").strip().lstrip("/")
        if not key:
            raise HTTPException(status_code=400, detail="文件 Key 不能为空")
        provider = get_storage_provider()
        logger.info("upload media file: driver={}, key={}", provider.driver, key)
        return await provider.upload(
            local_path,
            UploadOptions(
                key=key,
                file_name=file_name or Path(local_path).name,
                mime_type=mime_type or mimetypes.guess_type(file_name or local_path)[0] or "",
            ),
        )

    async def delete(self, key: str) -> None:
        normalized_key = self.normalize_key(key)
        if not normalized_key or normalized_key.startswith(("http://", "https://")):
            return
        provider = get_storage_provider()
        logger.info("delete media file: driver={}, key={}", provider.driver, normalized_key)
        await provider.delete(normalized_key)

    def get_public_url(self, key: str) -> str:
        normalized_key = self.normalize_key(key)
        if not normalized_key:
            return ""
        if normalized_key.startswith(("http://", "https://")):
            return normalized_key
        return get_storage_provider().get_public_url(normalized_key)

    def serialize_object_key(self, stored_value: str | None) -> str:
        normalized_key = self.normalize_key(stored_value)
        if not normalized_key:
            return ""
        if normalized_key.startswith(("http://", "https://")):
            return normalized_key
        return self.get_public_url(normalized_key)

    def serialize_stored_url(self, stored_value: str | None) -> str:
        return self.serialize_object_key(stored_value)

    def normalize_key(self, value: str | None) -> str:
        normalized = str(value or "").strip()
        if not normalized:
            return ""
        provider_key = get_storage_provider().normalize_key(normalized)
        if provider_key and provider_key != normalized:
            return provider_key.strip().lstrip("/")
        if not normalized.startswith(("http://", "https://")):
            return self._strip_local_upload_prefix(normalized)
        return self._extract_legacy_url_key(normalized)

    async def _save_upload_file(self, upload_file: UploadFile) -> str:
        os.makedirs(settings.PRODUCT_IMPORT_TMP_DIR, exist_ok=True)
        suffix = Path(self.sanitize_filename(upload_file.filename or "file")).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=settings.PRODUCT_IMPORT_TMP_DIR) as temp_file:
            temp_path = temp_file.name
            file_size = 0
            while True:
                chunk = await upload_file.read(self.chunk_size)
                if not chunk:
                    break
                file_size += len(chunk)
                self._validate_size(file_size)
                temp_file.write(chunk)
        if file_size <= 0:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=400, detail="文件内容不能为空")
        return temp_path

    @staticmethod
    def _validate_size(file_size: int) -> None:
        if file_size > settings.MEDIA_UPLOAD_MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail="文件大小超出系统限制")

    @staticmethod
    def _strip_local_upload_prefix(value: str) -> str:
        normalized = str(value or "").strip().lstrip("/")
        if normalized.startswith("uploads/"):
            return normalized[len("uploads/") :]
        return normalized

    def _extract_legacy_url_key(self, value: str) -> str:
        parsed = urlsplit(value)
        public_bases = [
            settings.LOCAL_STORAGE_PUBLIC_BASE_URL,
            settings.R2_PUBLIC_BASE_URL,
            settings.QINIU_PUBLIC_BASE_URL,
            self._legacy_qiniu_public_base_url(),
        ]
        for public_base in public_bases:
            key = self._extract_key_by_public_base(parsed, public_base)
            if key:
                return key
        return value

    @staticmethod
    def _extract_key_by_public_base(parsed_value, public_base: str) -> str:
        normalized_base = str(public_base or "").strip().rstrip("/")
        if not normalized_base:
            return ""
        if normalized_base.startswith("/"):
            base_path = normalized_base.strip("/")
            value_path = parsed_value.path.strip("/")
            if value_path.startswith(base_path + "/"):
                return value_path[len(base_path) + 1 :]
            return ""
        parsed_base = urlsplit(normalized_base)
        if parsed_value.netloc != parsed_base.netloc:
            return ""
        base_path = parsed_base.path.strip("/")
        value_path = parsed_value.path.strip("/")
        if base_path and value_path.startswith(base_path + "/"):
            return value_path[len(base_path) + 1 :]
        if not base_path:
            return value_path
        return ""

    @staticmethod
    def _legacy_qiniu_public_base_url() -> str:
        domain = str(settings.QINIU_DOMAIN or "").strip()
        if not domain:
            return ""
        if domain.startswith(("http://", "https://")):
            return domain.rstrip("/")
        return f"{str(settings.QINIU_DOMAIN_SCHEME or 'https').strip() or 'https'}://{domain.lstrip('/')}".rstrip("/")


media_storage_service = MediaStorageService()
