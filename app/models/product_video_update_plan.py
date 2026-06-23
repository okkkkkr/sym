from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import ProductVideoUpdatePlanStatus


class ProductVideoUpdatePlan(BaseModel, TimestampMixin):
    product_id = fields.BigIntField(description="好物ID", index=True)
    status = fields.CharEnumField(
        ProductVideoUpdatePlanStatus,
        default=ProductVideoUpdatePlanStatus.ACTIVE,
        description="计划状态",
        index=True,
    )
    items = fields.JSONField(default=list, description="视频条目序列")
    previous_video_keys = fields.JSONField(default=list, description="保存前视频 Key 列表")
    created_by = fields.BigIntField(description="创建人ID", index=True)
    error_message = fields.TextField(null=True, description="错误信息")

    class Meta:
        table = "product_video_update_plan"
