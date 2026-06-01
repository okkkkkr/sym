from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class HotBindingOption(BaseModel):
    id: int
    name: str = Field(..., description="名称")


class CategoryHotConfigUpdate(BaseModel):
    id: int = Field(..., description="类目ID")
    hot_brand_ids: list[int] = Field(default_factory=list, description="热门品牌ID列表")
    hot_tag_ids: list[int] = Field(default_factory=list, description="热门标签ID列表")


class CategoryHotConfigOut(BaseModel):
    id: int
    hot_brand_ids: list[int] = Field(default_factory=list, description="热门品牌ID列表")
    hot_tag_ids: list[int] = Field(default_factory=list, description="热门标签ID列表")
    brands: list[HotBindingOption] = Field(default_factory=list, description="可选品牌列表")
    tags: list[HotBindingOption] = Field(default_factory=list, description="可选标签列表")


class BaseCategory(BaseModel):
    name: str = Field(..., description="类目名称", example="BAG")
    desc: Optional[str] = Field(None, description="类目描述", example="箱包")
    order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")


class CategoryCreate(BaseCategory): ...


class CategoryInheritIn(BaseModel):
    source_id: int = Field(..., description="源类目ID")
    target_id: int = Field(..., description="目标类目ID")


class CategoryUpdate(BaseCategory):
    id: int


class CategoryImportItem(BaseCategory): ...


class CategoryInheritResult(BaseModel):
    source_id: int
    target_id: int
    transferred_brand_count: int = Field(0, description="转移品牌数量")
    transferred_hot_brand_count: int = Field(0, description="转移热门品牌数量")
    transferred_hot_tag_count: int = Field(0, description="转移热门标签数量")
    transferred_product_count: int = Field(0, description="转移好物数量")


class CategoryOut(BaseCategory):
    id: int
    hot_brand_ids: list[int] = Field(default_factory=list, description="热门品牌ID列表")
    hot_tag_ids: list[int] = Field(default_factory=list, description="热门标签ID列表")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
