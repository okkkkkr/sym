from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BaseContact(BaseModel):
    platform: str = Field(..., description="平台标识", example="wechat")
    display_name: str = Field(..., description="展示名称", example="微信公众号")
    contact_type: Optional[str] = Field(None, description="联系方式类型", example="qr")
    contact_value: Optional[str] = Field(None, description="联系方式值")
    link_url: Optional[str] = Field(None, description="跳转链接")
    qr_image_url: Optional[str] = Field(None, description="二维码图片")
    order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")


class ContactCreate(BaseContact): ...


class ContactUpdate(BaseContact):
    id: int


class ContactOut(BaseContact):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None