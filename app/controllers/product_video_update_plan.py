from app.core.crud import CRUDBase
from app.models.product_video_update_plan import ProductVideoUpdatePlan


class ProductVideoUpdatePlanController(CRUDBase[ProductVideoUpdatePlan, dict, dict]):
    def __init__(self):
        super().__init__(model=ProductVideoUpdatePlan)


product_video_update_plan_controller = ProductVideoUpdatePlanController()
