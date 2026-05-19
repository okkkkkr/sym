from datetime import datetime

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.banner import banner_controller
from app.controllers.brand import brand_controller
from app.controllers.category import category_controller
from app.controllers.product import product_controller
from app.models.admin import SiteVisit
from app.schemas.base import SuccessExtra

router = APIRouter()


async def serialize_brand_stats_payload(brand_obj):
    item = await brand_obj.to_dict()
    categories = [await category.to_dict() for category in await brand_obj.categories.all()]
    item["categories"] = categories
    item["category_ids"] = [category["id"] for category in categories]
    item["category"] = categories[0] if categories else None
    return item


@router.get("/site-visit/list", summary="查看访问量数据")
async def list_site_visit_stats(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="访客标识或用户代理关键字"),
    region: str = Query("", description="所属区域"),
    start_time: datetime | None = Query(None, description="开始时间"),
    end_time: datetime | None = Query(None, description="结束时间"),
):
    q = Q()
    if keyword:
        q &= Q(visitor_id__icontains=keyword) | Q(user_agent__icontains=keyword)
    if region:
        q &= Q(region__icontains=region)
    if start_time and end_time:
        q &= Q(visited_at__range=[start_time, end_time])
    elif start_time:
        q &= Q(visited_at__gte=start_time)
    elif end_time:
        q &= Q(visited_at__lte=end_time)

    total = await SiteVisit.filter(q).count()
    visit_objs = await SiteVisit.filter(q).offset((page - 1) * page_size).limit(page_size).order_by("-visited_at", "-id")
    data = [await visit_obj.to_dict() for visit_obj in visit_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/product-click/list", summary="查看好物点击数据")
async def list_product_click_stats(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="关键字"),
    category_id: int | None = Query(None, description="类目ID"),
    brand_id: int | None = Query(None, description="品牌ID"),
    status: bool | None = Query(None, description="是否上架"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q = Q(click_count__gt=0)
    if keyword:
        q &= Q(name__contains=keyword)
    if category_id is not None:
        q &= Q(category_id=category_id)
    if brand_id is not None:
        q &= Q(brand_id=brand_id)
    if status is not None:
        q &= Q(status=status)

    order = product_controller.build_order(
        default_order=["-click_count", "order", "-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"click_count", "updated_at", "order", "name", "status"},
    )
    total, product_objs = await product_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
    )
    data = []
    for obj in product_objs:
        item = await obj.to_dict()
        item["category"] = await (await category_controller.get(id=item["category_id"])).to_dict()
        item["brand"] = await (await brand_controller.get(id=item["brand_id"])).to_dict()
        data.append(item)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/brand-search/list", summary="查看品牌检索数据")
async def list_brand_search_stats(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="品牌名称"),
    category_id: int | None = Query(None, description="类目ID"),
    is_active: bool | None = Query(None, description="是否启用"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q = Q(search_count__gt=0)
    if name:
        q &= Q(name__contains=name)
    if category_id is not None:
        q &= Q(categories__id=category_id)
    if is_active is not None:
        q &= Q(is_active=is_active)

    order = brand_controller.build_order(
        default_order=["-search_count", "order", "-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"search_count", "updated_at", "order", "name", "is_active"},
    )
    total, brand_objs = await brand_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
    )
    data = []
    for obj in brand_objs:
        data.append(await serialize_brand_stats_payload(obj))
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/banner-click/list", summary="查看横幅点击数据")
async def list_banner_click_stats(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="横幅内容或活动备注"),
    is_active: bool | None = Query(None, description="是否启用"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q = Q(click_count__gt=0)
    if keyword:
        q &= Q(content__contains=keyword) | Q(note__contains=keyword)
    if is_active is not None:
        q &= Q(is_active=is_active)

    order = banner_controller.build_order(
        default_order=["-click_count", "-priority", "-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"click_count", "updated_at", "priority", "content", "is_active"},
    )
    total, banner_objs = await banner_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
    )
    data = [await obj.to_dict() for obj in banner_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)