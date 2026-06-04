from fastapi import APIRouter

from app.models import User
from app.core.dependency import DependAuth
from app.schemas.base import Success
from app.schemas.media import MediaDeleteIn
from app.services.media_cleanup import delete_media_keys

router = APIRouter()


@router.post("/delete", summary="删除媒体文件")
async def delete_media(payload: MediaDeleteIn, current_user: User = DependAuth):
    _ = current_user
    deleted_keys = await delete_media_keys(payload.keys)
    return Success(msg="Deleted Successfully", data={"deleted_keys": deleted_keys})
