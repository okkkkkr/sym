from fastapi import APIRouter

from .home_layouts import router

home_layouts_router = APIRouter()
home_layouts_router.include_router(router, tags=["首页装修模块"])

__all__ = ["home_layouts_router"]
