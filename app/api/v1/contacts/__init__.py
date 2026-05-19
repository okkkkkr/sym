from fastapi import APIRouter

from .contacts import router

contacts_router = APIRouter()
contacts_router.include_router(router, tags=["联系方式模块"])

__all__ = ["contacts_router"]