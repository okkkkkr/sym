from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class ProductTagOut(BaseModel):
    id: int
    name: str = Field(..., description="标签名称")


class BaseProduct(BaseModel):
    category_id: int = Field(..., description="类目ID")
    brand_id: int = Field(..., description="品牌ID")
    tag_ids: list[int] = Field(default_factory=list, description="标签ID列表")
    name: str = Field(..., description="好物名称")
    product_code_custom: Optional[str] = Field(None, description="好物识别码自定义数字")
    desc: Optional[str] = Field(None, description="好物简介")
    detail_description: list[Any] = Field(default_factory=list, description="结构化详情")
    cover_image_key: str = Field(..., description="封面图对象 Key")
    image_keys: list[str] = Field(default_factory=list, description="图片对象 Key 列表")
    video_keys: list[str] = Field(default_factory=list, description="视频对象 Key 列表")
    click_count: int = Field(0, description="点击量")
    status: bool = Field(True, description="是否上架")
    order: int = Field(0, description="排序")


class ProductCreate(BaseProduct): ...


class ProductUpdate(BaseProduct):
    id: int


class ProductOut(BaseProduct):
    id: int
    tags: list[ProductTagOut] = Field(default_factory=list, description="标签列表")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ProductMediaUploadTokenIn(BaseModel):
    file_name: str = Field(..., min_length=1, description="原始文件名")
    media_type: Literal["cover", "image", "video"] = Field(..., description="媒体类型")
    content_type: Optional[str] = Field(None, description="文件 MIME 类型")
