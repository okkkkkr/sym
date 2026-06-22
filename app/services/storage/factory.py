from functools import lru_cache

from app.settings import settings

from .base import StorageProvider
from .local import LocalStorageProvider
from .qiniu import QiniuProvider
from .s3 import S3StorageProvider


def get_storage_driver() -> str:
    return str(settings.STORAGE_DRIVER or settings.STORAGE_PROVIDER or "local").strip().lower()


@lru_cache(maxsize=1)
def get_storage_provider() -> StorageProvider:
    driver = get_storage_driver()
    if driver == "local":
        return LocalStorageProvider()
    if driver == "s3":
        return S3StorageProvider()
    if driver == "qiniu":
        return QiniuProvider()
    raise RuntimeError(f"unsupported storage driver: {driver}")


def validate_storage_provider() -> None:
    get_storage_provider().validate_config()
