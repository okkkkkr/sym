from urllib.parse import urlsplit

from pydantic import BaseModel, Field, field_validator


def validate_full_url(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        return ""
    parts = urlsplit(normalized)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError(f"{field_name} 必须是完整的 http(s) URL")
    return normalized


class SiteConfigUpdate(BaseModel):
    logo_url: str = Field(default="", max_length=500, description="站点 Logo URL")
    about_title: str = Field(default="", max_length=100, description="About 标题")
    about_lines: list[str] = Field(default_factory=list, description="About 文案段落")
    footer_disclaimer: str = Field(default="", max_length=500, description="底部声明")
    share_base_url: str = Field(default="", max_length=500, description="渠道分享基础链接")

    @field_validator("logo_url", "about_title", "footer_disclaimer", mode="before")
    @classmethod
    def normalize_text(cls, value):
        return str(value or "").strip()

    @field_validator("share_base_url", mode="before")
    @classmethod
    def normalize_share_base_url(cls, value):
        return validate_full_url(str(value or ""), "share_base_url")

    @field_validator("about_lines", mode="before")
    @classmethod
    def normalize_about_lines(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            value = value.splitlines()
        if not isinstance(value, list):
            raise ValueError("about_lines 必须是字符串数组")
        return [str(item).strip() for item in value if str(item).strip()]


class SiteConfigLogoUploadTokenIn(BaseModel):
    file_name: str = Field(..., min_length=1, description="原始文件名")
    content_type: str = Field(default="", description="文件 MIME 类型")


class SiteConfigLogoDeleteIn(BaseModel):
    logo_url: str = Field(default="", max_length=500, description="待删除的站点 Logo URL")

    @field_validator("logo_url", mode="before")
    @classmethod
    def normalize_logo_url(cls, value):
        return str(value or "").strip()
