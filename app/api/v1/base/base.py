import asyncio
import re
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException, Query, Request
from tortoise.expressions import F, Q

from app.controllers.brand import brand_controller
from app.controllers.banner import banner_controller
from app.controllers.category import category_controller
from app.controllers.contact import contact_controller
from app.controllers.product import product_controller
from app.controllers.tag import tag_controller
from app.controllers.user import user_controller
from app.core.ctx import CTX_USER_ID
from app.core.dependency import DependAuth
from app.models.admin import Api, AuditLog, Banner, Brand, Category, Contact, Menu, Product, Role, SiteVisit, User
from app.schemas.base import Fail, Success
from app.schemas.login import *
from app.schemas.stats import TrackBrandSearchIn, TrackProductClickIn, TrackSiteVisitIn
from app.schemas.users import UpdatePassword
from app.settings import settings
from app.utils.jwt_utils import create_access_token
from app.utils.password import get_password_hash, verify_password

router = APIRouter()


CATEGORY_KEY_PATTERN = re.compile(r"[^a-z0-9]+")


@router.post("/access_token", summary="获取token")
async def login_access_token(credentials: CredentialsSchema):
    user: User = await user_controller.authenticate(credentials)
    await user_controller.update_last_login(user.id)
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    expire = datetime.now(timezone.utc) + access_token_expires

    data = JWTOut(
        access_token=create_access_token(
            data=JWTPayload(
                user_id=user.id,
                username=user.username,
                is_superuser=user.is_superuser,
                exp=expire,
            )
        ),
        username=user.username,
    )
    return Success(data=data.model_dump())


@router.get("/userinfo", summary="查看用户信息", dependencies=[DependAuth])
async def get_userinfo():
    user_id = CTX_USER_ID.get()
    user_obj = await user_controller.get(id=user_id)
    data = await user_obj.to_dict(exclude_fields=["password"])
    data["avatar"] = "https://avatars.githubusercontent.com/u/54677442?v=4"
    return Success(data=data)


@router.get("/usermenu", summary="查看用户菜单", dependencies=[DependAuth])
async def get_user_menu():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    menus: list[Menu] = []
    if user_obj.is_superuser:
        menus = await Menu.all()
    else:
        role_objs: list[Role] = await user_obj.roles
        for role_obj in role_objs:
            menu = await role_obj.menus
            menus.extend(menu)
        menus = list(set(menus))

    menu_map = {menu.id: menu for menu in menus}
    pending_parent_ids = {menu.parent_id for menu in menus if menu.parent_id and menu.parent_id not in menu_map}
    while pending_parent_ids:
        parent_objs = await Menu.filter(id__in=list(pending_parent_ids))
        pending_parent_ids = set()
        for parent in parent_objs:
            if parent.id in menu_map:
                continue
            menu_map[parent.id] = parent
            if parent.parent_id and parent.parent_id not in menu_map:
                pending_parent_ids.add(parent.parent_id)
    menus = list(menu_map.values())

    parent_menus: list[Menu] = []
    for menu in menus:
        if menu.parent_id == 0:
            parent_menus.append(menu)
    res = []
    for parent_menu in parent_menus:
        parent_menu_dict = await parent_menu.to_dict()
        parent_menu_dict["children"] = []
        for menu in menus:
            if menu.parent_id == parent_menu.id:
                parent_menu_dict["children"].append(await menu.to_dict())
        res.append(parent_menu_dict)
    return Success(data=res)


@router.get("/userapi", summary="查看用户API", dependencies=[DependAuth])
async def get_user_api():
    user_id = CTX_USER_ID.get()
    user_obj = await User.filter(id=user_id).first()
    if user_obj.is_superuser:
        api_objs: list[Api] = await Api.all()
        apis = [api.method.lower() + api.path for api in api_objs]
        return Success(data=apis)
    role_objs: list[Role] = await user_obj.roles
    apis = []
    for role_obj in role_objs:
        api_objs: list[Api] = await role_obj.apis
        apis.extend([api.method.lower() + api.path for api in api_objs])
    apis = list(set(apis))
    return Success(data=apis)


@router.post("/update_password", summary="修改密码", dependencies=[DependAuth])
async def update_user_password(req_in: UpdatePassword):
    user_id = CTX_USER_ID.get()
    user = await user_controller.get(user_id)
    verified = verify_password(req_in.old_password, user.password)
    if not verified:
        return Fail(msg="旧密码验证错误！")
    user.password = get_password_hash(req_in.new_password)
    await user.save()
    return Success(msg="修改成功")


@router.get("/contacts", summary="查看启用的联系方式")
async def get_active_contacts(contact_type: str = ""):
    q = Q(is_active=True)
    if contact_type:
        q &= Q(contact_type=contact_type)
    _, contact_objs = await contact_controller.list(page=1, page_size=999, search=q, order=["order", "id"])
    return Success(data=[await obj.to_dict() for obj in contact_objs])


@router.get("/banners", summary="查看启用的横幅")
async def get_active_banners():
    _, banner_objs = await banner_controller.list(
        page=1,
        page_size=999,
        search=Q(is_active=True),
        order=["-priority", "id"],
    )
    return Success(data=[await obj.to_dict() for obj in banner_objs])


def serialize_dashboard_product(product_obj):
    return {
        "id": product_obj.id,
        "name": product_obj.name,
        "click_count": product_obj.click_count,
        "status": product_obj.status,
        "updated_at": product_obj.updated_at.strftime(settings.DATETIME_FORMAT) if product_obj.updated_at else None,
    }


def serialize_dashboard_brand(brand_obj):
    return {
        "id": brand_obj.id,
        "name": brand_obj.name,
        "search_count": brand_obj.search_count,
        "is_active": brand_obj.is_active,
        "updated_at": brand_obj.updated_at.strftime(settings.DATETIME_FORMAT) if brand_obj.updated_at else None,
    }


async def serialize_dashboard_log(log_obj):
    return {
        "id": log_obj.id,
        "username": log_obj.username,
        "module": log_obj.module,
        "summary": log_obj.summary,
        "method": log_obj.method,
        "path": log_obj.path,
        "status": log_obj.status,
        "created_at": log_obj.created_at.strftime(settings.DATETIME_FORMAT) if log_obj.created_at else None,
    }


@router.get("/dashboard_overview", summary="查看工作台概览", dependencies=[DependAuth])
async def get_dashboard_overview():
    now = datetime.now()
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=999999)

    (
        product_total,
        active_product_total,
        category_total,
        active_category_total,
        brand_total,
        active_brand_total,
        contact_total,
        active_contact_total,
        banner_total,
        active_banner_total,
        today_audit_total,
        today_visit_total,
        top_product_objs,
        top_brand_objs,
        recent_log_objs,
    ) = await asyncio.gather(
        Product.all().count(),
        Product.filter(status=True).count(),
        Category.all().count(),
        Category.filter(is_active=True).count(),
        Brand.all().count(),
        Brand.filter(is_active=True).count(),
        Contact.all().count(),
        Contact.filter(is_active=True).count(),
        Banner.all().count(),
        Banner.filter(is_active=True).count(),
        AuditLog.filter(created_at__range=[start_of_day, end_of_day]).count(),
        SiteVisit.filter(visited_at__range=[start_of_day, end_of_day]).count(),
        Product.all().order_by("-click_count", "order", "id").limit(10),
        Brand.all().order_by("-search_count", "order", "id").limit(10),
        AuditLog.all().order_by("-created_at").limit(6),
    )

    return Success(
        data={
            "product_total": product_total,
            "active_product_total": active_product_total,
            "inactive_product_total": max(product_total - active_product_total, 0),
            "category_total": category_total,
            "active_category_total": active_category_total,
            "inactive_category_total": max(category_total - active_category_total, 0),
            "brand_total": brand_total,
            "active_brand_total": active_brand_total,
            "inactive_brand_total": max(brand_total - active_brand_total, 0),
            "contact_total": contact_total,
            "active_contact_total": active_contact_total,
            "inactive_contact_total": max(contact_total - active_contact_total, 0),
            "banner_total": banner_total,
            "active_banner_total": active_banner_total,
            "inactive_banner_total": max(banner_total - active_banner_total, 0),
            "today_audit_total": today_audit_total,
            "today_visit_total": today_visit_total,
            "top_products": [serialize_dashboard_product(item) for item in top_product_objs],
            "top_brands": [serialize_dashboard_brand(item) for item in top_brand_objs],
            "recent_logs": [await serialize_dashboard_log(item) for item in recent_log_objs],
        }
    )


@router.post("/track/product-click", summary="上报前台好物点击")
async def track_product_click(payload: TrackProductClickIn):
    updated_count = await Product.filter(id=payload.product_id, status=True).update(click_count=F("click_count") + 1)
    if not updated_count:
        raise HTTPException(status_code=404, detail="Product not found")

    return Success(data={"tracked": True, "product_id": payload.product_id})


@router.post("/track/brand-search", summary="上报前台品牌筛选")
async def track_brand_search(payload: TrackBrandSearchIn):
    if not payload.brand_ids:
        return Success(data={"tracked": False, "brand_count": 0})

    updated_count = await Brand.filter(id__in=payload.brand_ids, is_active=True).update(search_count=F("search_count") + 1)
    return Success(data={"tracked": updated_count > 0, "brand_count": updated_count})


@router.post("/track/site-visit", summary="上报站点访问")
async def track_site_visit(payload: TrackSiteVisitIn, request: Request):
    visit_obj = await SiteVisit.create(
        visitor_id=payload.visitor_id,
        path=payload.path,
        user_agent=request.headers.get("user-agent", "")[:500],
    )

    return Success(
        data={
            "tracked": True,
            "visit_id": visit_obj.id,
            "visited_at": visit_obj.visited_at.strftime(settings.DATETIME_FORMAT),
        }
    )


def normalize_category_key(value: str | None) -> str:
    normalized = CATEGORY_KEY_PATTERN.sub("-", str(value or "").strip().lower()).strip("-")
    return normalized


def serialize_public_category(category_obj, brand_count: int = 0, product_count: int = 0):
    category_key = normalize_category_key(category_obj.name) or f"category-{category_obj.id}"
    return {
        "id": str(category_obj.id),
        "key": category_key,
        "name": category_obj.name,
        "label": str(category_obj.name or "").upper(),
        "description": category_obj.desc or "",
        "brandCount": brand_count,
        "productCount": product_count,
    }


async def get_public_categories_snapshot():
    category_objs = await category_controller.model.filter(is_active=True).order_by("order", "id")
    brand_objs = await brand_controller.model.filter(is_active=True).prefetch_related("categories")
    product_objs = await product_controller.model.filter(status=True).all()

    brand_count_map = {}
    for brand_obj in brand_objs:
        for category_obj in await brand_obj.categories.all():
            brand_count_map[category_obj.id] = brand_count_map.get(category_obj.id, 0) + 1

    product_count_map = {}
    for product_obj in product_objs:
        product_count_map[product_obj.category_id] = product_count_map.get(product_obj.category_id, 0) + 1

    category_items = []
    category_map = {}
    for category_obj in category_objs:
        category_item = serialize_public_category(
            category_obj,
            brand_count=brand_count_map.get(category_obj.id, 0),
            product_count=product_count_map.get(category_obj.id, 0),
        )
        category_items.append(category_item)
        category_map[category_item["key"]] = category_obj

    return category_items, category_map


def resolve_catalog_category(category_key: str, category_items: list[dict], category_map: dict):
    normalized_key = normalize_category_key(category_key)
    if normalized_key and normalized_key in category_map:
        return normalized_key, category_map[normalized_key]

    if not category_items:
        return "", None

    fallback_key = category_items[0]["key"]
    return fallback_key, category_map[fallback_key]


@router.get("/categories", summary="查看前台分类导航")
async def get_public_categories():
    category_items, _ = await get_public_categories_snapshot()
    return Success(data=category_items)


def normalize_detail_text(detail_description):
    if not isinstance(detail_description, list):
        return ""
    content = [str(item.get("content", "")).strip() for item in detail_description if isinstance(item, dict)]
    detail_text = " ".join(item for item in content if item)
    return "" if detail_text == "请输入结构化详情内容" else detail_text


def serialize_catalog_product(product_dict, category_key: str, brand_name: str):
    detail_text = normalize_detail_text(product_dict.get("detail_description"))
    return {
        "id": str(product_dict["id"]),
        "name": product_dict["name"],
        "productCode": product_dict.get("product_code") or "",
        "description": product_dict.get("desc") or detail_text,
        "detailDescription": detail_text or product_dict.get("desc") or "",
        "category": category_key,
        "brandName": brand_name,
        "coverImageUrl": product_dict.get("cover_image_url"),
        "imageUrls": product_dict.get("image_urls") or [],
        "videoUrls": product_dict.get("video_urls") or [],
        "clickCount": product_dict.get("click_count", 0),
    }


@router.get("/catalog", summary="查看前台好物目录")
async def get_catalog(
    category: str = Query("bag", description="类目标识"),
    keyword: str = Query("", description="关键字"),
    brand: str = Query("", description="品牌ID列表，逗号分隔"),
    tag: str = Query("", description="标签ID列表，逗号分隔"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(24, ge=1, le=100, description="每页数量"),
):
    category_items, category_map = await get_public_categories_snapshot()
    category_key, category_obj = resolve_catalog_category(category, category_items, category_map)
    if not category_obj:
        return Success(
            data={
                "category": "",
                "categoryLabel": "",
                "brands": [],
                "hotBrands": [],
                "hotTags": [],
                "products": [],
                "total": 0,
                "page": 1,
                "pageSize": page_size,
            }
        )

    category_name = category_obj.name
    keyword = keyword.strip()
    brand_ids = [int(item.strip()) for item in brand.split(",") if item.strip().isdigit()]
    tag_ids = [int(item.strip()) for item in tag.split(",") if item.strip().isdigit()]
    product_q = Q(category_id=category_obj.id, status=True)
    if brand_ids:
        product_q &= Q(brand_id__in=brand_ids)
    if tag_ids:
        product_q &= Q(tags__id__in=tag_ids)
    if keyword:
        product_q &= (Q(name__contains=keyword) | Q(desc__contains=keyword) | Q(tags__name__contains=keyword))

    catalog_order = ["order", "-click_count", "-updated_at", "-id"]
    all_products = await Product.filter(category_id=category_obj.id, status=True).prefetch_related("tags").order_by(*catalog_order)
    filtered_query = Product.filter(product_q).distinct()
    total = await filtered_query.count()
    filtered_products = await filtered_query.offset((page - 1) * page_size).limit(page_size).order_by(*catalog_order)
    _, brands = await brand_controller.list(
        page=1,
        page_size=999,
        search=Q(categories__id=category_obj.id, is_active=True),
        order=["order", "-updated_at", "-id"],
    )
    hot_brand_objs = await category_obj.hot_brands.filter(is_active=True).order_by("order", "-updated_at", "-id")
    hot_tag_objs = await category_obj.hot_tags.filter(is_active=True).order_by("sort", "-updated_at", "-id")

    brand_count_map = {}
    tag_count_map = {}
    for product_obj in all_products:
        brand_count_map[product_obj.brand_id] = brand_count_map.get(product_obj.brand_id, 0) + 1
        for tag_obj in await product_obj.tags.all():
            tag_count_map[tag_obj.id] = tag_count_map.get(tag_obj.id, 0) + 1

    brand_name_map = {brand_obj.id: brand_obj.name for brand_obj in brands}

    return Success(
        data={
            "category": category_key,
            "categoryLabel": str(category_name).upper(),
            "brands": [
                {"id": str(brand_obj.id), "name": brand_obj.name, "count": brand_count_map.get(brand_obj.id, 0)}
                for brand_obj in brands
            ],
            "hotBrands": [
                {"id": str(brand_obj.id), "name": brand_obj.name, "count": brand_count_map.get(brand_obj.id, 0)}
                for brand_obj in hot_brand_objs
            ],
            "hotTags": [
                {"id": str(tag_obj.id), "name": tag_obj.name, "count": tag_count_map.get(tag_obj.id, 0)}
                for tag_obj in hot_tag_objs
            ],
            "products": [
                serialize_catalog_product(await product_obj.to_dict(), category_key, brand_name_map.get(product_obj.brand_id, "SYM Studio"))
                for product_obj in filtered_products
            ],
            "total": total,
            "page": page,
            "pageSize": page_size,
        }
    )


@router.get("/catalog/products/{product_id}", summary="查看前台好物详情")
async def get_catalog_product(product_id: int):
    product_obj = await product_controller.get(id=product_id)
    if not product_obj.status:
        raise HTTPException(status_code=404, detail="Product not found")

    category_obj, brand_obj = await product_controller.ensure_relations(product_obj.category_id, product_obj.brand_id)
    category_key = normalize_category_key(category_obj.name) or f"category-{category_obj.id}"
    _, related_candidates = await product_controller.list(
        page=1,
        page_size=20,
        search=Q(category_id=product_obj.category_id, status=True),
        order=["order", "-click_count", "-updated_at", "-id"],
    )
    related_products = [item for item in related_candidates if item.id != product_obj.id][:5]

    return Success(
        data={
            "category": category_key,
            "categoryLabel": str(category_obj.name).upper(),
            "brandName": brand_obj.name,
            "product": serialize_catalog_product(await product_obj.to_dict(), category_key, brand_obj.name),
            "relatedProducts": [
                serialize_catalog_product(
                    await item.to_dict(),
                    category_key,
                    (await brand_controller.get(id=item.brand_id)).name,
                )
                for item in related_products
            ],
        }
    )
