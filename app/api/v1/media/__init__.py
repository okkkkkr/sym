from fastapi import APIRouter

from .media import router

media_router = APIRouter()
media_router.include_router(router, tags=["媒体模块"])

__all__ = ["media_router"]
