from fastapi import APIRouter

from app.controllers.site_config import serialize_site_config, site_config_controller
from app.schemas.base import Success
from app.schemas.site_configs import SiteConfigUpdate

router = APIRouter()


@router.get("/get", summary="查看站点配置")
async def get_site_config():
    return Success(data=serialize_site_config(await site_config_controller.get_singleton()))


@router.post("/update", summary="更新站点配置")
async def update_site_config(site_config_in: SiteConfigUpdate):
    site_config_obj = await site_config_controller.update_singleton(site_config_in)
    return Success(data=serialize_site_config(site_config_obj), msg="Updated Successfully")
