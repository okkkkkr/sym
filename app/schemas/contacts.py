from datetime import datetime
from typing import Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator

from app.schemas.sortable import nullable_rank_validator

DEFAULT_CONTACT_QR_IMAGE_URL = "https://os.alipayobjects.com/rmsportal/QBnOOoLaAfKPirc.png"


def normalize_contact_qr_image_url(value: str | None) -> str:
    normalized = str(value or "").strip()
    if not normalized or normalized == DEFAULT_CONTACT_QR_IMAGE_URL:
        return ""
    if not normalized.startswith(("http://", "https://")):
        return normalized.lstrip("/")

    path = urlsplit(normalized).path.lstrip("/")
    if path.startswith("uploads/contacts/"):
        return path[len("uploads/") :]
    if path.startswith("contacts/"):
        return path
    return normalized


class BaseContact(BaseModel):
    platform: str = Field(..., description="平台标识", example="wechat")
    display_name: str = Field(..., description="展示名称", example="微信公众号")
    contact_type: Optional[str] = Field(None, description="联系方式类型", example="qr")
    contact_value: Optional[str] = Field(None, description="联系方式值")
    link_url: Optional[str] = Field(None, description="跳转链接")
    qr_image_url: Optional[str] = Field(None, description="二维码图片")
    order: int | None = Field(None, description="排序")
    is_active: bool = Field(True, description="是否启用")

    @field_validator("platform", "display_name", "contact_type", "contact_value", "link_url", mode="before")
    @classmethod
    def normalize_text(cls, value):
        if value is None:
            return None
        return str(value).strip()

    @field_validator("qr_image_url", mode="before")
    @classmethod
    def normalize_qr_image_url(cls, value):
        return normalize_contact_qr_image_url(value)

    _validate_order = nullable_rank_validator("order")


class ContactCreate(BaseContact): ...


class ContactUpdate(BaseContact):
    id: int


class ContactOut(BaseContact):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ContactQrUploadTokenIn(BaseModel):
    file_name: str = Field(..., min_length=1, description="原始文件名")
    content_type: str = Field(default="", description="文件 MIME 类型")
