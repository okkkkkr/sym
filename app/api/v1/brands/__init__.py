from fastapi import APIRouter

from .brands import router

brands_router = APIRouter()
brands_router.include_router(router, tags=["品牌模块"])

__all__ = ["brands_router"]