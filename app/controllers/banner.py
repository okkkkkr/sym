from app.core.crud import CRUDBase
from app.models.admin import Banner
from app.schemas.banners import BannerCreate, BannerUpdate


class BannerController(CRUDBase[Banner, BannerCreate, BannerUpdate]):
    def __init__(self):
        super().__init__(model=Banner)


banner_controller = BannerController()