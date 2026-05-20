from fastapi import APIRouter

from .imports import router as import_router
from .products import router

products_router = APIRouter()
products_router.include_router(router, tags=["好物模块"])
products_router.include_router(import_router, tags=["好物导入"])

__all__ = ["products_router"]