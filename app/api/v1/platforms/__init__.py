from fastapi import APIRouter

from .platforms import router

platforms_router = APIRouter()
platforms_router.include_router(router, tags=["渠道模块"])

__all__ = ["platforms_router"]
