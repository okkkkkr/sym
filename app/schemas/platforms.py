import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


CUSTOM_NAME_PATTERN = re.compile(r"^[a-z0-9_-]+$")


class BasePlatform(BaseModel):
    platform_name: str = Field(..., min_length=1, max_length=100, description="渠道名称")
    custom_name: str = Field(..., min_length=1, max_length=50, description="自定义标识")

    @field_validator("platform_name")
    @classmethod
    def normalize_platform_name(cls, value: str):
        return value.strip()

    @field_validator("custom_name")
    @classmethod
    def normalize_custom_name(cls, value: str):
        normalized = value.strip()
        if not CUSTOM_NAME_PATTERN.fullmatch(normalized):
            raise ValueError("custom_name 仅允许小写字母、数字、短横线和下划线")
        return normalized


class PlatformCreate(BasePlatform): ...


class PlatformUpdate(BasePlatform):
    id: int


class PlatformOut(BasePlatform):
    id: int
    click_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
