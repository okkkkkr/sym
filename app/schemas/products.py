from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, field_validator

from app.schemas.sortable import nullable_rank_validator
from app.utils.product_media import sort_media_keys


class ProductTagOut(BaseModel):
    id: int
    name: str = Field(..., description="标签名称")


class ProductVideoItemIn(BaseModel):
    type: Literal["key", "resource"] = Field(..., description="视频条目类型")
    value: str | int = Field(..., description="key 或 resource id")

    @field_validator("value")
    @classmethod
    def normalize_value(cls, value: str | int):
        if isinstance(value, str):
            normalized_value = value.strip()
            if not normalized_value:
                raise ValueError("video item value is required")
            return normalized_value
        return value


class BaseProduct(BaseModel):
    category_id: int = Field(..., description="类目ID")
    brand_id: int = Field(..., description="品牌ID")
    tag_ids: list[int] = Field(default_factory=list, description="标签ID列表")
    name: str = Field(..., description="好物名称")
    product_code_custom: Optional[str] = Field(None, description="好物识别码自定义字符串")
    desc: Optional[str] = Field(None, description="好物简介")
    detail_description: list[Any] = Field(default_factory=list, description="结构化详情")
    cover_image_key: str = Field(..., description="封面图对象 Key")
    image_keys: list[str] = Field(default_factory=list, description="图片对象 Key 列表")
    video_keys: list[str] = Field(default_factory=list, description="视频对象 Key 列表")
    video_items: list[ProductVideoItemIn] | None = Field(default=None, description="视频条目序列")
    click_count: int = Field(0, description="点击量")
    status: bool = Field(True, description="是否上架")
    order: int | None = Field(None, description="排序")

    @field_validator("product_code_custom")
    @classmethod
    def validate_product_code_custom(cls, value: Optional[str]) -> Optional[str]:
        normalized_value = str(value or "").strip()
        return normalized_value or None

    @field_validator("image_keys")
    @classmethod
    def normalize_image_keys(cls, value: list[str]) -> list[str]:
        return sort_media_keys(list(dict.fromkeys(item for item in value if item)))

    _validate_order = nullable_rank_validator("order")


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
