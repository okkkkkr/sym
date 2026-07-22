from fastapi import APIRouter

from app.controllers.video_resource import video_resource_controller
from app.core.dependency import DependAuth
from app.models import User
from app.models.enums import VideoResourceStatus
from app.schemas.base import Success
from app.schemas.media import MediaDeleteIn
from app.services.media_cleanup import delete_owned_transient_media_keys
from app.services.media_storage import media_storage_service
from app.services.video_processing import video_processing_service

router = APIRouter()


@router.post("/delete", summary="删除媒体文件")
async def delete_media(payload: MediaDeleteIn, current_user: User = DependAuth):
    deleted_keys = []
    video_resource_ids = []
    for item in payload.keys:
        if str(item).startswith("video-resource:"):
            try:
                video_resource_ids.append(int(str(item).split(":", 1)[1]))
            except (TypeError, ValueError):
                continue
        else:
            deleted_keys.append(item)

    for resource_id in video_resource_ids:
        resource = await video_resource_controller.model.get_or_none(id=resource_id)
        if not resource:
            continue
        if not current_user.is_superuser and resource.created_by != current_user.id:
            continue
        if resource.product_id or resource.update_plan_id:
            continue
        if resource.storage_key:
            await media_storage_service.delete(resource.storage_key)
        video_processing_service.cleanup_file(resource.original_file_path)
        video_processing_service.cleanup_file(resource.compressed_file_path)
        await video_resource_controller.update(
            id=resource.id,
            obj_in={
                "status": VideoResourceStatus.FAILED,
                "error_message": "资源已删除",
                "original_file_path": "",
                "compressed_file_path": "",
            },
        )

    deleted_keys = await delete_owned_transient_media_keys(deleted_keys, current_user.id)
    return Success(msg="Deleted Successfully", data={"deleted_keys": deleted_keys})
