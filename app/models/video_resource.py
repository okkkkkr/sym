from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import VideoResourceStatus


class VideoResource(BaseModel, TimestampMixin):
    status = fields.CharEnumField(VideoResourceStatus, default=VideoResourceStatus.PENDING, description="处理状态")
    original_file_name = fields.CharField(max_length=255, description="原始文件名")
    original_file_path = fields.CharField(max_length=500, description="原始临时文件路径")
    compressed_file_path = fields.CharField(max_length=500, null=True, description="压缩后临时文件路径")
    product_id = fields.BigIntField(null=True, description="关联好物ID", index=True)
    update_plan_id = fields.BigIntField(null=True, description="视频更新计划ID", index=True)
    storage_provider = fields.CharField(max_length=50, default="", description="存储驱动")
    storage_key = fields.CharField(max_length=500, default="", description="对象 Key")
    public_url = fields.CharField(max_length=500, default="", description="公开访问地址")
    original_size = fields.BigIntField(default=0, description="原始文件大小")
    compressed_size = fields.BigIntField(null=True, description="压缩后文件大小")
    error_message = fields.TextField(null=True, description="错误信息")
    created_by = fields.BigIntField(description="上传人ID", index=True)

    class Meta:
        table = "video_resource"
