from fastapi import APIRouter

from app.core.dependency import DependPermission

from .brands import brands_router
from .banners import banners_router
from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .categories import categories_router
from .contacts import contacts_router
from .depts import depts_router
from .menus import menus_router
from .products import products_router
from .platforms import platforms_router
from .roles import roles_router
from .site_configs import site_configs_router
from .stats import stats_router
from .tags import tags_router
from .users import users_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(categories_router, prefix="/category", dependencies=[DependPermission])
v1_router.include_router(brands_router, prefix="/brand", dependencies=[DependPermission])
v1_router.include_router(banners_router, prefix="/banner", dependencies=[DependPermission])
v1_router.include_router(contacts_router, prefix="/contact", dependencies=[DependPermission])
v1_router.include_router(products_router, prefix="/product", dependencies=[DependPermission])
v1_router.include_router(platforms_router, prefix="/platform", dependencies=[DependPermission])
v1_router.include_router(site_configs_router, prefix="/site-config", dependencies=[DependPermission])
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])
v1_router.include_router(stats_router, prefix="/stats", dependencies=[DependPermission])
v1_router.include_router(tags_router, prefix="/tag", dependencies=[DependPermission])
