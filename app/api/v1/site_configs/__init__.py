from fastapi import APIRouter

from .site_configs import router

site_configs_router = APIRouter()
site_configs_router.include_router(router, tags=["站点配置模块"])

__all__ = ["site_configs_router"]
