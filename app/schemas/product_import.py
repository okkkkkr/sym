from typing import Any

from pydantic import BaseModel, Field


class ProductImportUploadInitIn(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255, description="原始文件名")
    file_size: int = Field(..., gt=0, description="文件总大小")
    total_chunks: int = Field(..., gt=0, description="总分片数")
    chunk_size: int = Field(..., gt=0, description="分片大小")
    import_strategy: str = Field(default="create_only", description="导入策略")


class ProductImportUploadInitOut(BaseModel):
    upload_id: str = Field(..., description="上传ID")
    task_id: int = Field(..., description="导入任务ID")
    uploaded_chunks: list[int] = Field(default_factory=list, description="已上传的分片索引")


class ProductImportUploadCompleteIn(BaseModel):
    upload_id: str = Field(..., min_length=1, description="上传ID")


class ProductImportUploadCompleteOut(BaseModel):
    task_id: int = Field(..., description="导入任务ID")
    merged_file_path: str = Field(..., description="合并后的本地文件路径")


class ProductImportParsedRow(BaseModel):
    row_no: int = Field(..., description="Excel行号")
    name: str = Field(..., description="好物名称")
    material_dir: str = Field(default="", description="素材目录")
    category_name: str = Field(default="", description="分类名称")
    brand_name: str = Field(default="", description="品牌名称")
    category_id: int | None = Field(default=None, description="分类ID")
    brand_id: int | None = Field(default=None, description="品牌ID")
    desc: str | None = Field(default=None, description="好物简介")
    tag_names: list[str] = Field(default_factory=list, description="标签名称列表")
    tag_ids: list[int] = Field(default_factory=list, description="标签ID列表")
    product_code_custom: str | None = Field(default=None, description="识别码自定义字符串")
    status: bool = Field(default=True, description="是否上架")
    order: int | None = Field(default=None, description="排序值")
    detail_description: list[Any] = Field(default_factory=list, description="结构化详情")
    duplicate_hint: bool = Field(default=False, description="是否疑似重复")
    errors: list[str] = Field(default_factory=list, description="预校验错误")
    warnings: list[str] = Field(default_factory=list, description="预校验提示")


class ProductImportParseResult(BaseModel):
    rows: list[ProductImportParsedRow] = Field(default_factory=list, description="解析后的数据行")
    headers: list[str] = Field(default_factory=list, description="实际表头")
    total_rows: int = Field(default=0, description="有效数据行数")
    valid_rows: int = Field(default=0, description="预校验通过数量")
    invalid_rows: int = Field(default=0, description="预校验失败数量")


class ProductImportMaterialSet(BaseModel):
    directory_name: str = Field(..., description="素材目录名")
    cover_image: str | None = Field(default=None, description="封面文件路径")
    images: list[str] = Field(default_factory=list, description="图片路径列表")
    videos: list[str] = Field(default_factory=list, description="视频路径列表")


class ProductImportTaskActionIn(BaseModel):
    task_id: int = Field(..., gt=0, description="导入任务ID")
