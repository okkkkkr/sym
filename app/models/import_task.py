from tortoise import fields

from .base import BaseModel, TimestampMixin
from .enums import ProductImportStrategy, ProductImportTaskItemStatus, ProductImportTaskStatus


class ProductImportTask(BaseModel, TimestampMixin):
    filename = fields.CharField(max_length=255, description="原始ZIP文件名")
    storage_key = fields.CharField(max_length=500, description="源文件存储定位信息")
    status = fields.CharEnumField(ProductImportTaskStatus, default=ProductImportTaskStatus.PENDING, description="任务状态")
    total_count = fields.IntField(default=0, description="模板总记录数")
    processed_count = fields.IntField(default=0, description="已处理数量")
    success_count = fields.IntField(default=0, description="成功数量")
    failed_count = fields.IntField(default=0, description="失败数量")
    progress = fields.IntField(default=0, description="进度百分比")
    import_strategy = fields.CharEnumField(
        ProductImportStrategy,
        default=ProductImportStrategy.CREATE_ONLY,
        description="导入策略",
    )
    error_message = fields.TextField(null=True, description="任务级错误摘要")
    result_summary = fields.JSONField(default=dict, description="结果汇总")
    error_report_path = fields.CharField(max_length=500, null=True, description="错误报告路径")
    created_by = fields.BigIntField(description="发起人ID", index=True)
    started_at = fields.DatetimeField(null=True, description="开始时间", index=True)
    finished_at = fields.DatetimeField(null=True, description="完成时间", index=True)

    class Meta:
        table = "product_import_task"


class ProductImportTaskItem(BaseModel, TimestampMixin):
    task = fields.ForeignKeyField("models.ProductImportTask", related_name="items", on_delete=fields.CASCADE)
    row_no = fields.IntField(description="Excel行号", index=True)
    product_name = fields.CharField(max_length=100, description="好物名称", index=True)
    status = fields.CharEnumField(
        ProductImportTaskItemStatus,
        default=ProductImportTaskItemStatus.PENDING,
        description="行级状态",
    )
    message = fields.TextField(null=True, description="处理结果信息")
    category_name = fields.CharField(max_length=100, null=True, description="分类名称快照", index=True)
    brand_name = fields.CharField(max_length=100, null=True, description="品牌名称快照", index=True)
    product_id = fields.BigIntField(null=True, description="创建成功后的好物ID", index=True)
    duplicate_hint = fields.BooleanField(default=False, description="是否疑似重复", index=True)

    class Meta:
        table = "product_import_task_item"