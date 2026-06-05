from datetime import datetime

from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.banner import banner_controller
from app.controllers.brand import brand_controller
from app.controllers.category import category_controller
from app.controllers.product import product_controller
from tortoise.functions import Count

from app.models.admin import ChannelVisit, Contact, ContactClick, Platform, SiteVisit
from app.schemas.base import SuccessExtra

router = APIRouter()


async def serialize_brand_stats_payload(brand_obj):
    item = await brand_obj.to_dict()
    categories = [await category.to_dict() for category in await brand_obj.categories.all()]
    item["categories"] = categories
    item["category_ids"] = [category["id"] for category in categories]
    item["category"] = categories[0] if categories else None
    return item


@router.get("/channel-visit/list", summary="查看渠道访问数据")
async def list_channel_visit_stats(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="渠道名称或自定义标识"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    platform_objs = await Platform.all()
    platform_map = {item.custom_name: item for item in platform_objs}
    count_rows = await ChannelVisit.all().group_by("custom_name").annotate(click_count=Count("id")).values(
        "custom_name", "click_count"
    )
    snapshot_rows = await ChannelVisit.all().order_by("-visited_at", "-id").values(
        "custom_name", "platform_name_snapshot"
    )
    snapshot_map = {}
    for item in snapshot_rows:
        snapshot_map.setdefault(item["custom_name"], item["platform_name_snapshot"])

    count_map = {item["custom_name"]: item["click_count"] for item in count_rows}
    custom_names = set(platform_map) | set(count_map)
    data = []
    for custom_name in custom_names:
        platform_obj = platform_map.get(custom_name)
        platform_name = platform_obj.platform_name if platform_obj else snapshot_map.get(custom_name, custom_name)
        if keyword and keyword not in platform_name and keyword not in custom_name:
            continue
        data.append(
            {
                "id": platform_obj.id if platform_obj else f"deleted-{custom_name}",
                "platform_name": platform_name,
                "custom_name": custom_name,
                "click_count": count_map.get(custom_name, 0),
                "status": "active" if platform_obj else "deleted",
            }
        )

    reverse = sort_order != "asc"
    if sort_field in {"platform_name", "custom_name"}:
        data.sort(key=lambda item: item[sort_field], reverse=reverse)
    else:
        data.sort(key=lambda item: (item["click_count"], item["custom_name"]), reverse=reverse)
    total = len(data)
    offset = (page - 1) * page_size
    return SuccessExtra(data=data[offset : offset + page_size], total=total, page=page, page_size=page_size)


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


@router.get("/contact-click/list", summary="查看联系方式点击数据")
async def list_contact_click_stats(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="平台、名称或联系内容关键字"),
    contact_type: str = Query("", description="联系方式类型"),
    status: str = Query("", description="状态 active/inactive/deleted"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    contact_objs = await Contact.filter(is_deleted=False).all()
    contact_map = {item.id: item for item in contact_objs}
    count_rows = await ContactClick.all().group_by("contact_id").annotate(click_count=Count("id")).values(
        "contact_id", "click_count"
    )
    snapshot_rows = await ContactClick.all().order_by("-clicked_at", "-id").values(
        "contact_id",
        "platform_snapshot",
        "display_name_snapshot",
        "contact_type_snapshot",
        "contact_value_snapshot",
    )

    snapshot_map = {}
    for item in snapshot_rows:
        snapshot_map.setdefault(item["contact_id"], item)

    count_map = {item["contact_id"]: item["click_count"] for item in count_rows}
    contact_ids = set(contact_map) | set(count_map)
    data = []
    for contact_id in contact_ids:
        contact_obj = contact_map.get(contact_id)
        snapshot = snapshot_map.get(contact_id, {})
        platform = contact_obj.platform if contact_obj else snapshot.get("platform_snapshot", "")
        display_name = contact_obj.display_name if contact_obj else snapshot.get("display_name_snapshot", f"联系方式 #{contact_id}")
        item_contact_type = contact_obj.contact_type if contact_obj else snapshot.get("contact_type_snapshot")
        contact_value = contact_obj.contact_value if contact_obj else snapshot.get("contact_value_snapshot")
        item_status = "deleted"
        if contact_obj:
            item_status = "active" if contact_obj.is_active else "inactive"

        if keyword and keyword not in platform and keyword not in display_name and keyword not in str(contact_value or ""):
            continue
        if contact_type and contact_type != item_contact_type:
            continue
        if status and status != item_status:
            continue

        data.append(
            {
                "id": contact_obj.id if contact_obj else f"deleted-{contact_id}",
                "contact_id": contact_id,
                "platform": platform,
                "display_name": display_name,
                "contact_type": item_contact_type,
                "contact_value": contact_value,
                "click_count": count_map.get(contact_id, 0),
                "status": item_status,
            }
        )

    reverse = sort_order != "asc"
    if sort_field in {"platform", "display_name", "contact_type", "status"}:
        data.sort(key=lambda item: str(item[sort_field] or ""), reverse=reverse)
    else:
        data.sort(key=lambda item: (item["click_count"], item["contact_id"]), reverse=reverse)
    total = len(data)
    offset = (page - 1) * page_size
    return SuccessExtra(data=data[offset : offset + page_size], total=total, page=page, page_size=page_size)


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

    annotations = None
    order = product_controller.build_order(
        default_order=["-click_count", "order", "-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"click_count", "updated_at", "order", "name", "status"},
    )
    if sort_field == "order" or sort_field is None:
        annotations, order = product_controller.build_nullable_field_order("order", ["-click_count", "-updated_at", "-id"], sort_order)
    total, product_objs = await product_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
        annotations=annotations,
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

    annotations = None
    order = brand_controller.build_order(
        default_order=["-search_count", "order", "-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"search_count", "updated_at", "order", "name", "is_active"},
    )
    if sort_field == "order" or sort_field is None:
        annotations, order = brand_controller.build_nullable_field_order("order", ["-search_count", "-updated_at", "-id"], sort_order)
    total, brand_objs = await brand_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
        annotations=annotations,
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

    annotations = None
    order = banner_controller.build_order(
        default_order=["-click_count", "priority", "-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"click_count", "updated_at", "priority", "content", "is_active"},
    )
    if sort_field == "priority" or sort_field is None:
        annotations, order = banner_controller.build_nullable_field_order("priority", ["-click_count", "-updated_at", "-id"], sort_order)
    total, banner_objs = await banner_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
        annotations=annotations,
    )
    data = [await obj.to_dict() for obj in banner_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)
