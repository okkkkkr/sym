import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import string
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

from fastapi import HTTPException

from app.settings import settings


QINIU_REGION_UPLOAD_HOSTS = {
    "z0": "https://up.qiniup.com",
    "cn-east-1": "https://up.qiniup.com",
    "huadong": "https://up.qiniup.com",
    "z1": "https://up-z1.qiniup.com",
    "cn-north-1": "https://up-z1.qiniup.com",
    "huabei": "https://up-z1.qiniup.com",
    "z2": "https://up-z2.qiniup.com",
    "cn-south-1": "https://up-z2.qiniup.com",
    "huanan": "https://up-z2.qiniup.com",
    "na0": "https://up-na0.qiniup.com",
    "us-north-1": "https://up-na0.qiniup.com",
    "beimei": "https://up-na0.qiniup.com",
    "as0": "https://up-as0.qiniup.com",
    "ap-southeast-1": "https://up-as0.qiniup.com",
    "xinjiapo": "https://up-as0.qiniup.com",
    "cn-east-2": "https://up-cn-east-2.qiniup.com",
}

PRODUCT_MEDIA_TYPE_RULES = {
    "logo": {
        "prefix": "logo",
        "file_prefix": "logo",
        "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".avif"},
        "mime_prefix": "image/",
    },
    "cover": {
        "prefix": "items/images",
        "file_prefix": "img",
        "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".avif"},
        "mime_prefix": "image/",
    },
    "image": {
        "prefix": "items/images",
        "file_prefix": "img",
        "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg", ".avif"},
        "mime_prefix": "image/",
    },
    "video": {
        "prefix": "items/videos",
        "file_prefix": "vid",
        "extensions": {".mp4", ".mov", ".m4v", ".webm", ".ogg", ".ogv", ".avi", ".mkv"},
        "mime_prefix": "video/",
    },
}

SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._-]+")


def _urlsafe_base64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode()


class ProductMediaUploadService:
    token_expires_in_seconds = 3600

    @staticmethod
    def _normalize_upload_host() -> str:
        normalized_region = str(settings.QINIU_REGION or "").strip().lower()
        if normalized_region.startswith(("http://", "https://")):
            return normalized_region.rstrip("/")
        if "." in normalized_region:
            return f"https://{normalized_region.lstrip('/')}".rstrip("/")
        upload_host = QINIU_REGION_UPLOAD_HOSTS.get(normalized_region)
        if upload_host:
            return upload_host
        raise HTTPException(status_code=500, detail="七牛上传区域配置无效")

    @staticmethod
    def _normalize_public_domain() -> str:
        normalized_domain = str(settings.QINIU_DOMAIN or "").strip()
        if not normalized_domain:
            raise HTTPException(status_code=500, detail="七牛访问域名未配置")
        normalized_scheme = str(settings.QINIU_DOMAIN_SCHEME or "https").strip().lower() or "https"
        if normalized_scheme not in {"http", "https"}:
            raise HTTPException(status_code=500, detail="七牛访问协议配置无效")
        if normalized_domain.startswith(("http://", "https://")):
            return normalized_domain.rstrip("/")
        return f"{normalized_scheme}://{normalized_domain.lstrip('/')}".rstrip("/")

    @staticmethod
    def _validate_settings() -> None:
        missing_names = [
            name
            for name, value in {
                "QINIU_ACCESS_KEY": settings.QINIU_ACCESS_KEY,
                "QINIU_SECRET_KEY": settings.QINIU_SECRET_KEY,
                "QINIU_BUCKET": settings.QINIU_BUCKET,
                "QINIU_DOMAIN": settings.QINIU_DOMAIN,
                "QINIU_DOMAIN_SCHEME": settings.QINIU_DOMAIN_SCHEME,
                "QINIU_REGION": settings.QINIU_REGION,
            }.items()
            if not str(value or "").strip()
        ]
        if missing_names:
            raise HTTPException(status_code=500, detail=f"七牛配置缺失: {', '.join(missing_names)}")

    @staticmethod
    def _sanitize_filename(file_name: str) -> str:
        base_name = os.path.basename(str(file_name or "").strip())
        name, extension = os.path.splitext(base_name)
        normalized_name = SAFE_FILENAME_PATTERN.sub("-", name).strip("-._") or "file"
        normalized_extension = extension.lower()
        return f"{normalized_name}{normalized_extension}"

    @staticmethod
    def _validate_media_type(media_type: str) -> dict:
        media_rule = PRODUCT_MEDIA_TYPE_RULES.get(str(media_type or "").strip().lower())
        if not media_rule:
            raise HTTPException(status_code=400, detail="不支持的媒体类型")
        return media_rule

    @staticmethod
    def _validate_file(file_name: str, content_type: str | None, media_rule: dict) -> None:
        normalized_name = ProductMediaUploadService._sanitize_filename(file_name)
        extension = os.path.splitext(normalized_name)[1].lower()
        if extension not in media_rule["extensions"]:
            raise HTTPException(status_code=400, detail="不支持的文件格式")

        guessed_content_type = str(content_type or "").strip().lower() or mimetypes.guess_type(normalized_name)[0] or ""
        if guessed_content_type and not guessed_content_type.startswith(media_rule["mime_prefix"]):
            raise HTTPException(status_code=400, detail="文件类型与媒体类型不匹配")

    @staticmethod
    def _build_object_key(media_type: str, file_name: str) -> str:
        normalized_name = ProductMediaUploadService._sanitize_filename(file_name)
        extension = os.path.splitext(normalized_name)[1].lower()
        media_rule = PRODUCT_MEDIA_TYPE_RULES[media_type]
        random_suffix = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(8))
        date_token = datetime.now().strftime("%Y%m%d")
        return f"{media_rule['prefix']}/{media_rule['file_prefix']}_{date_token}_{random_suffix}{extension}"

    @staticmethod
    def _build_upload_token(object_key: str) -> str:
        deadline = int(
            (
                datetime.now(timezone.utc)
                + timedelta(seconds=ProductMediaUploadService.token_expires_in_seconds)
            ).timestamp()
        )
        put_policy = {
            "scope": f"{settings.QINIU_BUCKET}:{object_key}",
            "deadline": deadline,
        }
        encoded_policy = _urlsafe_base64(json.dumps(put_policy, separators=(",", ":")).encode())
        digest = hmac.new(
            str(settings.QINIU_SECRET_KEY).encode(),
            encoded_policy.encode(),
            hashlib.sha1,
        ).digest()
        encoded_digest = _urlsafe_base64(digest)
        return f"{settings.QINIU_ACCESS_KEY}:{encoded_digest}:{encoded_policy}"

    @staticmethod
    def _sign_download_path(path_with_query: str) -> str:
        digest = hmac.new(
            str(settings.QINIU_SECRET_KEY).encode(),
            path_with_query.encode(),
            hashlib.sha1,
        ).digest()
        return _urlsafe_base64(digest)

    def is_private_bucket(self) -> bool:
        return bool(settings.QINIU_IS_PRIVATE)

    def build_public_url(self, object_key: str) -> str:
        return f"{self._normalize_public_domain()}/{object_key.lstrip('/')}"

    def build_private_url(self, object_key: str, expires_in: int | None = None) -> str:
        base_url = self.build_public_url(object_key)
        deadline = int(
            (
                datetime.now(timezone.utc)
                + timedelta(seconds=max(1, int(expires_in or settings.QINIU_URL_EXPIRE_SECONDS)))
            ).timestamp()
        )
        separator = "&" if "?" in base_url else "?"
        path_with_query = f"{base_url}{separator}e={deadline}"
        token = self._sign_download_path(path_with_query)
        return f"{path_with_query}&token={settings.QINIU_ACCESS_KEY}:{token}"

    def build_access_url(self, object_key: str, expires_in: int | None = None) -> str:
        self._validate_settings()
        if self.is_private_bucket():
            return self.build_private_url(object_key, expires_in=expires_in)
        return self.build_public_url(object_key)

    def extract_object_key(self, stored_value: str | None) -> str | None:
        if not stored_value:
            return None
        normalized = str(stored_value).strip()
        if not normalized:
            return None
        if not normalized.startswith(("http://", "https://")):
            return normalized.lstrip("/")
        if not str(settings.QINIU_DOMAIN or "").strip():
            return None
        public_domain = self._normalize_public_domain()
        if normalized.startswith(public_domain + "/"):
            return normalized[len(public_domain) + 1 :].split("?", 1)[0]
        parsed_url = urlsplit(normalized)
        parsed_domain = urlsplit(public_domain)
        if parsed_url.netloc and parsed_url.netloc == parsed_domain.netloc:
            return parsed_url.path.lstrip("/").split("?", 1)[0]
        return None

    def serialize_object_key(self, stored_value: str | None, expires_in: int | None = None) -> str:
        object_key = self.extract_object_key(stored_value)
        if not object_key:
            return str(stored_value or "")
        return self.build_access_url(object_key, expires_in=expires_in)

    def serialize_stored_url(self, stored_value: str | None, expires_in: int | None = None) -> str:
        return self.serialize_object_key(stored_value, expires_in=expires_in)

    def create_upload_credentials(self, file_name: str, media_type: str, content_type: str | None = None) -> dict:
        self._validate_settings()
        media_rule = self._validate_media_type(media_type)
        self._validate_file(file_name, content_type, media_rule)
        object_key = self._build_object_key(media_type, file_name)
        return {
            "upload_token": self._build_upload_token(object_key),
            "upload_url": self._normalize_upload_host(),
            "object_key": object_key,
            "url": self.build_public_url(object_key),
            "preview_url": self.build_access_url(object_key),
            "media_type": media_type,
        }

    def create_site_logo_upload_credentials(self, file_name: str, content_type: str | None = None) -> dict:
        return self.create_upload_credentials(file_name=file_name, media_type="logo", content_type=content_type)


product_media_upload_service = ProductMediaUploadService()
