from fastapi import APIRouter, File, HTTPException, UploadFile

from app.controllers.site_config import serialize_site_config, site_config_controller
from app.core.dependency import DependAuth
from app.models import User
from app.schemas.base import Success
from app.schemas.site_configs import SiteConfigLogoDeleteIn, SiteConfigLogoUploadTokenIn, SiteConfigUpdate
from app.services.media_cleanup import delete_owned_transient_media_keys
from app.services.media_storage import media_storage_service

router = APIRouter()


@router.get("/get", summary="查看站点配置")
async def get_site_config():
    return Success(
        data=serialize_site_config(await site_config_controller.get_singleton(), include_storage=True, include_key=True)
    )


@router.post("/logo/upload-token", summary="获取站点 Logo 上传凭证")
async def get_site_logo_upload_token(payload: SiteConfigLogoUploadTokenIn, current_user: User = DependAuth):
    _ = current_user
    _ = payload
    raise HTTPException(status_code=410, detail="上传凭证接口已废弃，请使用后端中转上传接口")


@router.post("/logo/upload", summary="上传站点 Logo")
async def upload_site_logo(file: UploadFile = File(...), current_user: User = DependAuth):
    return Success(data=await media_storage_service.upload(file, "logo", current_user.id))


@router.post("/logo/delete", summary="删除站点 Logo 文件")
async def delete_site_logo(payload: SiteConfigLogoDeleteIn, current_user: User = DependAuth):
    await delete_owned_transient_media_keys([payload.logo_key], current_user.id)
    return Success(msg="Deleted Successfully")


@router.post("/update", summary="更新站点配置")
async def update_site_config(site_config_in: SiteConfigUpdate):
    site_config_obj = await site_config_controller.update_singleton(site_config_in)
    return Success(
        data=serialize_site_config(site_config_obj, include_storage=True, include_key=True), msg="Updated Successfully"
    )
