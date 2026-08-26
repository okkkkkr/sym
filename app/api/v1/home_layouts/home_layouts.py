from fastapi import APIRouter, File, HTTPException, UploadFile

from app.controllers.home_layout import home_layout_controller
from app.core.dependency import DependAuth
from app.models import User
from app.schemas.base import Success
from app.schemas.home_layouts import (
    HomeLayoutDraftSaveIn,
    HomeLayoutImageUploadTokenIn,
    HomeLayoutPublishIn,
)
from app.services.media_storage import media_storage_service

router = APIRouter()


@router.get("/draft", summary="查看首页装修草稿")
async def get_home_layout_draft():
    return Success(data=await home_layout_controller.get_draft_data())


@router.post("/image/upload-token", summary="获取首页装修图片上传凭证")
async def get_home_layout_image_upload_token(payload: HomeLayoutImageUploadTokenIn, current_user: User = DependAuth):
    _ = current_user
    _ = payload
    raise HTTPException(status_code=410, detail="上传凭证接口已废弃，请使用后端中转上传接口")


@router.post("/image/upload", summary="上传首页装修图片")
async def upload_home_layout_image(file: UploadFile = File(...), current_user: User = DependAuth):
    return Success(data=await media_storage_service.upload(file, "home_layout", current_user.id))


@router.post("/draft/save", summary="保存首页装修草稿")
async def save_home_layout_draft(payload: HomeLayoutDraftSaveIn):
    return Success(data=await home_layout_controller.save_draft(payload), msg="Saved Successfully")


@router.post("/publish", summary="发布首页装修")
async def publish_home_layout(payload: HomeLayoutPublishIn):
    return Success(data=await home_layout_controller.publish(payload.page_code), msg="Published Successfully")


@router.get("/current", summary="查看当前发布首页装修")
async def get_current_home_layout():
    return Success(data=await home_layout_controller.get_current_admin_data())
