from fastapi import APIRouter

from app.settings import settings

from .products import router

products_router = APIRouter()
products_router.include_router(router, tags=["好物模块"])
if settings.PRODUCT_IMPORT_ENABLED:
    from .imports import router as import_router

    products_router.include_router(import_router, tags=["好物导入"])

__all__ = ["products_router"]
