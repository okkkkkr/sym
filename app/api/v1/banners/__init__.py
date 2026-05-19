from fastapi import APIRouter

from .banners import router

banners_router = APIRouter()
banners_router.include_router(router, tags=["横幅模块"])

__all__ = ["banners_router"]