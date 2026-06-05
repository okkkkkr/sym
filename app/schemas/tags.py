from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.sortable import nullable_rank_validator


class BaseTag(BaseModel):
    name: str = Field(..., description="标签名称", example="Travel")
    remark: Optional[str] = Field(None, description="备注")
    search_count: int = Field(0, description="检索次数")
    sort: int | None = Field(None, description="排序")
    is_active: bool = Field(True, description="是否启用")

    _validate_sort = nullable_rank_validator("sort")


class TagCreate(BaseTag): ...


class TagUpdate(TagCreate):
    id: int


class TagImportItem(BaseTag): ...


class TagOut(BaseTag):
    id: int
    product_count: int = Field(0, description="已关联好物数量")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
