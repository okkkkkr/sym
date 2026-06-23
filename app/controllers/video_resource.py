from app.core.crud import CRUDBase
from app.models.video_resource import VideoResource


class VideoResourceController(CRUDBase[VideoResource, dict, dict]):
    def __init__(self):
        super().__init__(model=VideoResource)


video_resource_controller = VideoResourceController()
