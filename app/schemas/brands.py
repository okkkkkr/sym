from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.sortable import nullable_rank_validator


class BaseBrand(BaseModel):
    category_ids: list[int] = Field(default_factory=list, description="类目ID列表")
    name: str = Field(..., description="品牌名称", example="SYMBOL")
    desc: Optional[str] = Field(None, description="品牌描述")
    search_count: int = Field(0, description="搜索次数")
    order: int | None = Field(None, description="排序")
    is_active: bool = Field(True, description="是否启用")

    _validate_order = nullable_rank_validator("order")


class BrandCreate(BaseBrand): ...


class BrandImportItem(BaseBrand): ...


class BrandUpdate(BaseBrand):
    id: int


class BrandInheritIn(BaseModel):
    source_id: int = Field(..., description="源品牌ID")
    target_id: int = Field(..., description="目标品牌ID")


class BrandInheritResult(BaseModel):
    source_id: int
    target_id: int
    transferred_product_count: int = Field(0, description="转移好物数量")


class BrandOut(BaseBrand):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
