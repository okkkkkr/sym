from tortoise import fields

from app.schemas.menus import MenuType

from .base import BaseModel, TimestampMixin
from .enums import MethodType


class User(BaseModel, TimestampMixin):
    username = fields.CharField(max_length=20, unique=True, description="用户名称", index=True)
    alias = fields.CharField(max_length=30, null=True, description="姓名", index=True)
    email = fields.CharField(max_length=255, unique=True, null=True, description="邮箱", index=True)
    phone = fields.CharField(max_length=20, null=True, description="电话", index=True)
    password = fields.CharField(max_length=128, null=True, description="密码")
    is_active = fields.BooleanField(default=True, description="是否激活", index=True)
    is_superuser = fields.BooleanField(default=False, description="是否为超级管理员", index=True)
    last_login = fields.DatetimeField(null=True, description="最后登录时间", index=True)
    roles = fields.ManyToManyField("models.Role", related_name="user_roles")
    dept_id = fields.IntField(null=True, description="部门ID", index=True)

    class Meta:
        table = "user"


class Role(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="角色名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="角色描述")
    menus = fields.ManyToManyField("models.Menu", related_name="role_menus")
    apis = fields.ManyToManyField("models.Api", related_name="role_apis")

    class Meta:
        table = "role"


class Api(BaseModel, TimestampMixin):
    path = fields.CharField(max_length=100, description="API路径", index=True)
    method = fields.CharEnumField(MethodType, description="请求方法", index=True)
    summary = fields.CharField(max_length=500, description="请求简介", index=True)
    tags = fields.CharField(max_length=100, description="API标签", index=True)

    class Meta:
        table = "api"


class Menu(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, description="菜单名称", index=True)
    remark = fields.JSONField(null=True, description="保留字段")
    menu_type = fields.CharEnumField(MenuType, null=True, description="菜单类型")
    icon = fields.CharField(max_length=100, null=True, description="菜单图标")
    path = fields.CharField(max_length=100, description="菜单路径", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, description="父菜单ID", index=True)
    is_hidden = fields.BooleanField(default=False, description="是否隐藏")
    component = fields.CharField(max_length=100, description="组件")
    keepalive = fields.BooleanField(default=True, description="存活")
    redirect = fields.CharField(max_length=100, null=True, description="重定向")

    class Meta:
        table = "menu"


class Dept(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=20, unique=True, description="部门名称", index=True)
    desc = fields.CharField(max_length=500, null=True, description="备注")
    is_deleted = fields.BooleanField(default=False, description="软删除标记", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    parent_id = fields.IntField(default=0, max_length=10, description="父部门ID", index=True)

    class Meta:
        table = "dept"


class DeptClosure(BaseModel, TimestampMixin):
    ancestor = fields.IntField(description="父代", index=True)
    descendant = fields.IntField(description="子代", index=True)
    level = fields.IntField(default=0, description="深度", index=True)


class AuditLog(BaseModel, TimestampMixin):
    user_id = fields.IntField(description="用户ID", index=True)
    username = fields.CharField(max_length=64, default="", description="用户名称", index=True)
    module = fields.CharField(max_length=64, default="", description="功能模块", index=True)
    summary = fields.CharField(max_length=128, default="", description="请求描述", index=True)
    method = fields.CharField(max_length=10, default="", description="请求方法", index=True)
    path = fields.CharField(max_length=255, default="", description="请求路径", index=True)
    status = fields.IntField(default=-1, description="状态码", index=True)
    response_time = fields.IntField(default=0, description="响应时间(单位ms)", index=True)
    request_args = fields.JSONField(null=True, description="请求参数")
    response_body = fields.JSONField(null=True, description="返回数据")


class SiteVisit(BaseModel):
    visitor_id = fields.CharField(max_length=64, description="访客标识", index=True)
    path = fields.CharField(max_length=255, default="/", description="访问路径", index=True)
    region = fields.CharField(max_length=100, default="", description="所属区域", index=True)
    user_agent = fields.CharField(max_length=500, default="", description="用户代理")
    visited_at = fields.DatetimeField(auto_now_add=True, description="访问时间", index=True)

    class Meta:
        table = "site_visit"


class Category(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, unique=True, description="类目名称", index=True)
    desc = fields.CharField(max_length=255, null=True, description="类目描述")
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)
    hot_tags = fields.ManyToManyField("models.Tag", related_name="hot_categories", through="category_hot_tag")

    class Meta:
        table = "category"


class Tag(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=100, unique=True, description="标签名称", index=True)
    remark = fields.CharField(max_length=255, null=True, description="备注")
    search_count = fields.IntField(default=0, description="检索次数", index=True)
    sort = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "tag"


class Brand(BaseModel, TimestampMixin):
    categories = fields.ManyToManyField("models.Category", related_name="brands")
    hot_categories = fields.ManyToManyField(
        "models.Category", related_name="hot_brands", through="brand_hot_category"
    )
    name = fields.CharField(max_length=100, description="品牌名称", index=True)
    desc = fields.CharField(max_length=255, null=True, description="品牌描述")
    search_count = fields.IntField(default=0, description="搜索次数", index=True)
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "brand"


class Contact(BaseModel, TimestampMixin):
    platform = fields.CharField(max_length=50, description="平台标识", index=True)
    display_name = fields.CharField(max_length=100, description="展示名称", index=True)
    contact_type = fields.CharField(max_length=30, null=True, description="联系方式类型", index=True)
    contact_value = fields.CharField(max_length=255, null=True, description="联系方式值")
    link_url = fields.CharField(max_length=500, null=True, description="跳转链接")
    qr_image_url = fields.CharField(max_length=500, null=True, description="二维码图片")
    order = fields.IntField(default=0, description="排序", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "contact"


class Banner(BaseModel, TimestampMixin):
    content = fields.CharField(max_length=255, description="横幅内容")
    note = fields.CharField(max_length=255, null=True, description="活动备注")
    priority = fields.IntField(default=0, description="优先级", index=True)
    link_url = fields.CharField(max_length=500, null=True, description="跳转路径")
    click_count = fields.IntField(default=0, description="点击量", index=True)
    is_active = fields.BooleanField(default=True, description="是否启用", index=True)

    class Meta:
        table = "banner"


class Product(BaseModel, TimestampMixin):
    tags = fields.ManyToManyField("models.Tag", related_name="products", through="product_tag")
    category_id = fields.BigIntField(description="类目ID", index=True)
    brand_id = fields.BigIntField(description="品牌ID", index=True)
    name = fields.CharField(max_length=100, unique=True, description="好物名称", index=True)
    product_code = fields.CharField(max_length=64, null=True, description="好物识别码", index=True)
    desc = fields.CharField(max_length=255, null=True, description="好物简介")
    detail_description = fields.JSONField(default=list, description="结构化详情")
    cover_image_url = fields.CharField(max_length=500, description="封面图")
    image_urls = fields.JSONField(default=list, description="图片列表")
    video_urls = fields.JSONField(default=list, description="视频列表")
    click_count = fields.IntField(default=0, description="点击量", index=True)
    status = fields.BooleanField(default=True, description="是否上架", index=True)
    order = fields.IntField(default=0, description="排序", index=True)

    class Meta:
        table = "product"
