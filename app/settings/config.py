import os
import typing
from json import loads as json_loads

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    VERSION: str = "0.1.0"
    APP_TITLE: str = "SYM Admin"
    PROJECT_NAME: str = "SYM Admin"
    APP_DESCRIPTION: str = "Description"

    CORS_ORIGINS: typing.List = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: typing.List = ["*"]
    CORS_ALLOW_HEADERS: typing.List = ["*"]

    DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 9999

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"debug", "development", "dev", "true", "1", "yes", "on"}:
                return True
            if normalized in {"release", "production", "prod", "false", "0", "no", "off"}:
                return False
        return value

    @field_validator("MEDIA_ORPHAN_CLEANUP_PREFIXES", mode="before")
    @classmethod
    def parse_media_orphan_cleanup_prefixes(cls, value):
        if value in (None, ""):
            return [
                "logo/",
                "contacts/",
                "home-layout/",
                "items/images/",
                "items/videos/",
            ]
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return []
            if normalized.startswith("["):
                parsed = json_loads(normalized)
                return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in normalized.split(",") if item.strip()]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()]
        return value

    PROJECT_ROOT: str = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    BASE_DIR: str = os.path.abspath(os.path.join(PROJECT_ROOT, os.pardir))
    LOGS_ROOT: str = os.path.join(BASE_DIR, "app/logs")
    PRODUCT_IMPORT_MAX_FILE_SIZE: int = 2 * 1024 * 1024 * 1024
    PRODUCT_IMPORT_TMP_DIR: str = os.path.join(BASE_DIR, "tmp", "product-import")
    VIDEO_UPLOAD_TMP_DIR: str = os.path.join(BASE_DIR, "tmp", "video-processing")
    PRODUCT_IMPORT_CHUNK_SIZE: int = 5 * 1024 * 1024
    PRODUCT_IMPORT_MAX_CONCURRENCY: int = 2
    PRODUCT_IMPORT_MAX_WORKERS: int = 4
    PRODUCT_IMPORT_CLEANUP_ENABLED: bool = True
    PRODUCT_IMPORT_CLEANUP_RETENTION_HOURS: int = 24
    PRODUCT_IMPORT_CLEANUP_INTERVAL_SECONDS: int = 3600
    MEDIA_ORPHAN_CLEANUP_ENABLED: bool = True
    MEDIA_ORPHAN_CLEANUP_DRY_RUN: bool = True
    MEDIA_ORPHAN_RETENTION_HOURS: int = 24
    MEDIA_ORPHAN_CLEANUP_INTERVAL_SECONDS: int = 21600
    MEDIA_ORPHAN_CLEANUP_BATCH_SIZE: int = 1000
    MEDIA_ORPHAN_CLEANUP_PREFIXES: typing.List[str] = [
        "logo/",
        "contacts/",
        "home-layout/",
        "items/images/",
        "items/videos/",
    ]
    STORAGE_DRIVER: str = ""
    STORAGE_PROVIDER: str = ""
    MEDIA_UPLOAD_MAX_FILE_SIZE: int = 500 * 1024 * 1024
    LOCAL_STORAGE_ROOT: str = os.path.join(BASE_DIR, "uploads")
    LOCAL_STORAGE_PUBLIC_BASE_URL: str = "/uploads"
    LOCAL_STORAGE_MAX_FILE_SIZE: int = 500 * 1024 * 1024
    S3_ENDPOINT_URL: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = ""
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_PUBLIC_BASE_URL: str = ""
    S3_FORCE_PATH_STYLE: bool = False
    R2_ENDPOINT_URL: str = ""
    R2_BUCKET: str = ""
    R2_REGION: str = "auto"
    R2_ACCESS_KEY: str = ""
    R2_SECRET_KEY: str = ""
    R2_PUBLIC_BASE_URL: str = ""
    R2_FORCE_PATH_STYLE: bool = True
    QINIU_ACCESS_KEY: str = ""
    QINIU_SECRET_KEY: str = ""
    QINIU_BUCKET: str = ""
    QINIU_PUBLIC_BASE_URL: str = ""
    QINIU_DOMAIN: str = ""
    QINIU_DOMAIN_SCHEME: str = "https"
    QINIU_REGION: str = ""
    QINIU_IS_PRIVATE: bool = False
    QINIU_URL_EXPIRE_SECONDS: int = 3600
    QINIU_UPLOAD_TIMEOUT_SECONDS: int = 300
    CERT_MONITOR_ENABLED: bool = True
    CERT_MONITOR_INTERVAL_SECONDS: int = 21600
    CERT_MONITOR_WARNING_DAYS: int = 30
    CERT_MONITOR_MAIN_CERT_PATH: str = os.path.join(
        BASE_DIR, "certbot", "conf", "live", "symluxlib.com", "fullchain.pem"
    )
    CERT_MONITOR_STATIC_CERT_PATH: str = os.path.join(BASE_DIR, "certs", "static.symluxlib.com", "fullchain.pem")
    PUBLIC_SITE_URL: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "sym"
    POSTGRES_PASSWORD: str = "sym"
    POSTGRES_DB: str = "sym"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    SECRET_KEY: str = "3488a63e1765035d386f05409663f55c83bfae3b3c61a932744b20ad14244dcf"  # openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 day
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    @property
    def TORTOISE_ORM(self) -> dict:
        return {
            "connections": {
                "postgres": {
                    "engine": "tortoise.backends.asyncpg",
                    "credentials": {
                        "host": self.POSTGRES_HOST,
                        "port": self.POSTGRES_PORT,
                        "user": self.POSTGRES_USER,
                        "password": self.POSTGRES_PASSWORD,
                        "database": self.POSTGRES_DB,
                    },
                },
            },
            "apps": {
                "models": {
                    "models": ["app.models", "aerich.models"],
                    "default_connection": "postgres",
                },
            },
            "use_tz": False,
            "timezone": "Asia/Shanghai",
        }


settings = Settings()
