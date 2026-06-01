from fastapi import APIRouter

from app.controllers.site_config import serialize_site_config, site_config_controller
from app.core.dependency import DependAuth
from app.models import User
from app.schemas.base import Success
from app.schemas.site_configs import SiteConfigLogoDeleteIn, SiteConfigLogoUploadTokenIn, SiteConfigUpdate
from app.services.product_media_upload import product_media_upload_service

router = APIRouter()


@router.get("/get", summary="查看站点配置")
async def get_site_config():
    return Success(data=serialize_site_config(await site_config_controller.get_singleton(), include_storage=True))


@router.post("/logo/upload-token", summary="获取站点 Logo 上传凭证")
async def get_site_logo_upload_token(payload: SiteConfigLogoUploadTokenIn, current_user: User = DependAuth):
    _ = current_user
    return Success(data=product_media_upload_service.create_site_logo_upload_credentials(**payload.model_dump()))


@router.post("/logo/delete", summary="删除站点 Logo 文件")
async def delete_site_logo(payload: SiteConfigLogoDeleteIn, current_user: User = DependAuth):
    _ = current_user
    await site_config_controller.delete_logo_file(payload.logo_url)
    return Success(msg="Deleted Successfully")


@router.post("/update", summary="更新站点配置")
async def update_site_config(site_config_in: SiteConfigUpdate):
    site_config_obj = await site_config_controller.update_singleton(site_config_in)
    return Success(data=serialize_site_config(site_config_obj, include_storage=True), msg="Updated Successfully")
