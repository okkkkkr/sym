from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.sortable import nullable_rank_validator


class BaseBanner(BaseModel):
    content: str = Field(..., description="横幅内容", example="新品上市，点击查看")
    note: Optional[str] = Field(None, description="活动备注")
    priority: int | None = Field(None, description="优先级")
    link_url: Optional[str] = Field(None, description="跳转路径")
    is_active: bool = Field(True, description="是否启用")

    _validate_priority = nullable_rank_validator("priority")


class BannerCreate(BaseBanner): ...


class BannerUpdate(BaseBanner):
    id: int


class BannerOut(BaseBanner):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
