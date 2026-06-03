from typing import Any, Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, Field, model_validator

MODULE_TYPES = {
    "single_image",
    "grid_2",
    "grid_4",
    "grid_8",
    "carousel",
    "horizontal_list",
}
CONFIG_RULES = {
    "single_image": {"ratio", "text_position", "overlay"},
    "grid_2": set(),
    "grid_4": set(),
    "grid_8": set(),
    "carousel": {"autoplay", "interval", "show_dots"},
    "horizontal_list": set(),
}
MODULE_ITEM_COUNTS = {
    "single_image": (1, 1),
    "grid_2": (2, 2),
    "grid_4": (4, 4),
    "grid_8": (8, 8),
    "carousel": (1, None),
    "horizontal_list": (1, None),
}
ACTION_TARGETS = {"self", "blank"}


class HomeLayoutCommonConfigIn(BaseModel):
    show_banner: bool = Field(default=True, description="是否显示横幅")
    show_navigation: bool = Field(default=True, description="是否显示导航")
    show_footer: bool = Field(default=True, description="是否显示底部")


def validate_link(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return ""
    if normalized.startswith("/"):
        return normalized
    parts = urlsplit(normalized)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise ValueError("link 必须是站内路径或完整的 http(s) URL")
    return normalized


class LayoutAction(BaseModel):
    text: str = Field(default="", max_length=100, description="操作文案")
    link: str = Field(default="", max_length=500, description="跳转地址")
    target: Literal["self", "blank"] = Field(default="self", description="打开方式")

    @model_validator(mode="after")
    def validate_action(self):
        self.text = self.text.strip()
        self.link = validate_link(self.link)
        if self.target not in ACTION_TARGETS:
            raise ValueError("target 配置无效")
        if self.text and not self.link:
            raise ValueError("配置操作文案时必须同时提供跳转地址")
        return self


class HomeLayoutItemIn(BaseModel):
    id: int | None = Field(default=None, description="内容项ID")
    sort: int = Field(default=0, description="排序")
    image: str = Field(default="", max_length=500, description="图片地址")
    title: str = Field(default="", max_length=255, description="主文案")
    description: str = Field(default="", max_length=500, description="辅助文案")
    badge: str = Field(default="", max_length=100, description="角标文案")
    action: LayoutAction = Field(default_factory=LayoutAction, description="内容项操作配置")

    @model_validator(mode="after")
    def normalize_item(self):
        self.image = self.image.strip()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.badge = self.badge.strip()
        return self


class HomeLayoutModuleIn(BaseModel):
    id: int | None = Field(default=None, description="模块ID")
    type: str = Field(..., description="模块类型")
    sort: int = Field(default=0, description="排序")
    is_enabled: bool = Field(default=True, description="是否启用")
    title: str = Field(default="", max_length=255, description="标题")
    action: LayoutAction = Field(default_factory=LayoutAction, description="模块操作配置")
    config: dict[str, Any] = Field(default_factory=dict, description="模块配置")
    items: list[HomeLayoutItemIn] = Field(default_factory=list, description="内容项列表")

    @model_validator(mode="after")
    def validate_module(self):
        self.type = self.type.strip()
        self.title = self.title.strip()
        if self.type not in MODULE_TYPES:
            raise ValueError("模块类型无效")
        allowed_config_keys = CONFIG_RULES[self.type]
        unsupported_keys = [key for key in self.config.keys() if key not in allowed_config_keys]
        if unsupported_keys:
            raise ValueError(f"{self.type} 不支持的 config 字段: {', '.join(unsupported_keys)}")
        min_count, max_count = MODULE_ITEM_COUNTS[self.type]
        item_count = len(self.items)
        if item_count < min_count:
            raise ValueError(f"{self.type} 至少需要 {min_count} 个内容项")
        if max_count is not None and item_count != max_count:
            raise ValueError(f"{self.type} 需要 {max_count} 个内容项")
        item_sorts = [item.sort for item in self.items]
        if len(item_sorts) != len(set(item_sorts)):
            raise ValueError("模块内 item.sort 不能重复")
        return self


class HomeLayoutDraftSaveIn(BaseModel):
    page_code: Literal["home"] = Field(default="home", description="页面标识")
    common_config: HomeLayoutCommonConfigIn = Field(default_factory=HomeLayoutCommonConfigIn, description="公共配置")
    modules: list[HomeLayoutModuleIn] = Field(default_factory=list, description="模块列表")

    @model_validator(mode="after")
    def validate_payload(self):
        module_sorts = [module.sort for module in self.modules]
        if len(module_sorts) != len(set(module_sorts)):
            raise ValueError("module.sort 不能重复")
        return self


class HomeLayoutPublishIn(BaseModel):
    page_code: Literal["home"] = Field(default="home", description="页面标识")


class HomeLayoutImageUploadTokenIn(BaseModel):
    file_name: str = Field(..., min_length=1, description="原始文件名")
    content_type: str = Field(default="", description="文件 MIME 类型")
