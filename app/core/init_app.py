from aerich import Command
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.models.admin import Api, Menu, Platform, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=[
                "/api/v1/base/access_token",
                "/docs",
                "/openapi.json",
            ],
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)


async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def init_platforms():
    await Platform.get_or_create(
        custom_name="nature",
        defaults={
            "platform_name": "自然流量",
            "click_count": 0,
        },
    )


async def init_menus():
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(children_menu)
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=True,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )

    top_menu = await Menu.filter(path="/top-menu", parent_id=0).first()
    top_menu_payload = dict(
        menu_type=MenuType.MENU,
        name="一级菜单",
        path="/top-menu",
        order=2,
        parent_id=0,
        icon="material-symbols:featured-play-list-outline",
        is_hidden=True,
        component="/top-menu",
        keepalive=False,
        redirect="",
    )
    if top_menu:
        top_menu.update_from_dict(top_menu_payload)
        await top_menu.save()
    else:
        await Menu.create(**top_menu_payload)

    system_menu = await Menu.filter(path="/system", parent_id=0).first()
    if not system_menu:
        system_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )

    content_menu = await Menu.filter(path="/content", parent_id=0).first()
    content_payload = dict(
        menu_type=MenuType.CATALOG,
        name="内容管理",
        path="/content",
        order=2,
        parent_id=0,
        icon="material-symbols:inventory-2-outline",
        is_hidden=False,
        component="Layout",
        keepalive=False,
        redirect="/content/category",
    )
    if content_menu:
        content_menu.update_from_dict(content_payload)
        await content_menu.save()
    else:
        content_menu = await Menu.create(**content_payload)

    data_menu = await Menu.filter(path="/data", parent_id=0).first()
    data_payload = dict(
        menu_type=MenuType.CATALOG,
        name="数据管理",
        path="/data",
        order=3,
        parent_id=0,
        icon="material-symbols:database-outline",
        is_hidden=False,
        component="Layout",
        keepalive=False,
        redirect="/data/site-visit",
    )
    if data_menu:
        data_menu.update_from_dict(data_payload)
        await data_menu.save()
    else:
        data_menu = await Menu.create(**data_payload)

    batch_menu = await Menu.filter(path="/batch", parent_id=0).first()
    batch_payload = dict(
        menu_type=MenuType.CATALOG,
        name="批量中心",
        path="/batch",
        order=4,
        parent_id=0,
        icon="material-symbols:upload-file-outline",
        is_hidden=False,
        component="Layout",
        keepalive=False,
        redirect="/batch/product-import",
    )
    if batch_menu:
        batch_menu.update_from_dict(batch_payload)
        await batch_menu.save()
    else:
        batch_menu = await Menu.create(**batch_payload)

    business_children = [
        {
            "name": "好物管理",
            "path": "product",
            "order": 7,
            "icon": "material-symbols:shopping-bag-outline",
            "component": "/system/product",
        },
        {
            "name": "分类管理",
            "path": "category",
            "order": 8,
            "icon": "material-symbols:category-outline",
            "component": "/system/category",
        },
        {
            "name": "品牌管理",
            "path": "brand",
            "order": 9,
            "icon": "mdi:tag-outline",
            "component": "/system/brand",
        },
        {
            "name": "标签管理",
            "path": "tag",
            "order": 10,
            "icon": "mdi:tag-multiple-outline",
            "component": "/system/tag",
        },
        {
            "name": "横幅管理",
            "path": "banner",
            "order": 11,
            "icon": "material-symbols:slideshow-outline",
            "component": "/system/banner",
        },
        {
            "name": "联系方式管理",
            "path": "contact",
            "order": 12,
            "icon": "material-symbols:contact-phone-outline",
            "component": "/system/contact",
        },
        {
            "name": "渠道管理",
            "path": "platform",
            "order": 13,
            "icon": "mdi:source-branch",
            "component": "/system/platform",
        },
        {
            "name": "站点配置",
            "path": "site-config",
            "order": 14,
            "icon": "material-symbols:settings-suggest-outline",
            "component": "/system/site-config",
        },
    ]

    for item in business_children:
        menu_obj = await Menu.filter(parent_id=content_menu.id, path=item["path"]).first()
        if not menu_obj:
            menu_obj = await Menu.filter(parent_id=system_menu.id, path=item["path"]).first()
        payload = dict(
            menu_type=MenuType.MENU,
            name=item["name"],
            path=item["path"],
            order=item["order"],
            parent_id=content_menu.id,
            icon=item["icon"],
            is_hidden=False,
            component=item["component"],
            keepalive=False,
        )
        if menu_obj:
            menu_obj.update_from_dict(payload)
            await menu_obj.save()
        else:
            await Menu.create(**payload)

    stats_children = [
        {
            "name": "访问量数据",
            "path": "site-visit",
            "order": 1,
            "icon": "carbon:chart-line-data",
            "component": "/data/site-visit",
        },
        {
            "name": "好物点击数据",
            "path": "product-click",
            "order": 2,
            "icon": "mdi:cursor-default-click-outline",
            "component": "/data/product-click",
        },
        {
            "name": "品牌检索数据",
            "path": "brand-search",
            "order": 3,
            "icon": "material-symbols:manage-search",
            "component": "/data/brand-search",
        },
        {
            "name": "横幅点击数据",
            "path": "banner-click",
            "order": 4,
            "icon": "mdi:bullhorn-outline",
            "component": "/data/banner-click",
        },
        {
            "name": "渠道访问数据",
            "path": "channel-visit",
            "order": 5,
            "icon": "carbon:chart-relationship",
            "component": "/data/channel-visit",
        },
        {
            "name": "联系方式点击数据",
            "path": "contact-click",
            "order": 6,
            "icon": "material-symbols:contact-phone-outline",
            "component": "/data/contact-click",
        },
    ]

    for item in stats_children:
        menu_obj = await Menu.filter(parent_id=data_menu.id, path=item["path"]).first()
        payload = dict(
            menu_type=MenuType.MENU,
            name=item["name"],
            path=item["path"],
            order=item["order"],
            parent_id=data_menu.id,
            icon=item["icon"],
            is_hidden=False,
            component=item["component"],
            keepalive=False,
        )
        if menu_obj:
            menu_obj.update_from_dict(payload)
            await menu_obj.save()
        else:
            await Menu.create(**payload)

    batch_children = [
        {
            "name": "好物批量导入",
            "path": "product-import",
            "order": 1,
            "icon": "material-symbols:upload-file-outline",
            "component": "/system/product-import",
        },
        {
            "name": "导入任务记录",
            "path": "product-import-task",
            "order": 2,
            "icon": "material-symbols:task-outline",
            "component": "/system/product-import-task",
        },
    ]

    for item in batch_children:
        menu_obj = await Menu.filter(parent_id=batch_menu.id, path=item["path"]).first()
        payload = dict(
            menu_type=MenuType.MENU,
            name=item["name"],
            path=item["path"],
            order=item["order"],
            parent_id=batch_menu.id,
            icon=item["icon"],
            is_hidden=False,
            component=item["component"],
            keepalive=False,
        )
        if menu_obj:
            menu_obj.update_from_dict(payload)
            await menu_obj.save()
        else:
            await Menu.create(**payload)


async def init_apis():
    await api_controller.refresh_api()


async def init_db():
    command = Command(tortoise_config=settings.TORTOISE_ORM)
    try:
        await command.init_db(safe=True)
    except FileExistsError:
        pass

    await command.init()
    await command.upgrade(run_in_transaction=True)


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)

    admin_role = await Role.filter(name="管理员").first()
    if admin_role:
        all_apis = await Api.all()
        all_menus = await Menu.all()
        await admin_role.apis.clear()
        await admin_role.apis.add(*all_apis)
        await admin_role.menus.clear()
        await admin_role.menus.add(*all_menus)


async def init_data():
    await init_db()
    await init_superuser()
    await init_platforms()
    await init_menus()
    await init_apis()
    await init_roles()
