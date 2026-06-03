from app.core.crud import CRUDBase
from app.models.admin import Platform
from app.schemas.platforms import PlatformCreate, PlatformUpdate


class PlatformController(CRUDBase[Platform, PlatformCreate, PlatformUpdate]):
    def __init__(self):
        super().__init__(model=Platform)


platform_controller = PlatformController()
