from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import Q
from tortoise.functions import Count

from app.controllers.platform import platform_controller
from app.controllers.site_config import site_config_controller
from app.models.admin import ChannelVisit
from app.schemas.base import Success, SuccessExtra
from app.schemas.platforms import PlatformCreate, PlatformUpdate

router = APIRouter()

NATURE_CUSTOM_NAME = "nature"


def build_share_url(custom_name: str, share_base_url: str) -> str:
    if custom_name == NATURE_CUSTOM_NAME or not share_base_url:
        return ""
    parts = urlsplit(share_base_url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query["plat"] = custom_name
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


async def get_click_count_map() -> dict[str, int]:
    rows = await ChannelVisit.all().group_by("custom_name").annotate(click_count=Count("id")).values(
        "custom_name", "click_count"
    )
    return {item["custom_name"]: item["click_count"] for item in rows}


async def get_share_base_url() -> str:
    site_config_obj = await site_config_controller.get_singleton()
    if not site_config_obj:
        return ""
    return str(site_config_obj.share_base_url or "").strip()


async def serialize_platform(platform_obj, click_count_map: dict[str, int], share_base_url: str):
    item = await platform_obj.to_dict()
    item["click_count"] = click_count_map.get(platform_obj.custom_name, 0)
    item["share_url"] = build_share_url(platform_obj.custom_name, share_base_url)
    item["is_system"] = platform_obj.custom_name == NATURE_CUSTOM_NAME
    return item


@router.get("/list", summary="查看渠道列表")
async def list_platform(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="渠道名称或自定义标识"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q = Q()
    if keyword:
        q &= Q(platform_name__contains=keyword) | Q(custom_name__contains=keyword)
    click_count_map, share_base_url = await get_click_count_map(), await get_share_base_url()
    if sort_field == "click_count":
        platform_objs = await platform_controller.model.filter(q)
        data = [await serialize_platform(obj, click_count_map, share_base_url) for obj in platform_objs]
        data.sort(key=lambda item: item["click_count"], reverse=sort_order != "asc")
        total = len(data)
        offset = (page - 1) * page_size
        return SuccessExtra(data=data[offset : offset + page_size], total=total, page=page, page_size=page_size)

    order = platform_controller.build_order(
        default_order=["-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"updated_at", "platform_name", "custom_name"},
    )
    total, platform_objs = await platform_controller.list(page=page, page_size=page_size, search=q, order=order)
    data = [await serialize_platform(obj, click_count_map, share_base_url) for obj in platform_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看渠道")
async def get_platform(id: int = Query(..., description="渠道ID")):
    platform_obj = await platform_controller.get(id=id)
    return Success(data=await serialize_platform(platform_obj, await get_click_count_map(), await get_share_base_url()))


@router.post("/create", summary="创建渠道")
async def create_platform(platform_in: PlatformCreate):
    if platform_in.custom_name == NATURE_CUSTOM_NAME:
        raise HTTPException(status_code=400, detail="nature 为系统保留标识")
    if await platform_controller.model.filter(custom_name=platform_in.custom_name).exists():
        raise HTTPException(status_code=400, detail="自定义名称已存在")
    await platform_controller.create(obj_in=platform_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新渠道")
async def update_platform(platform_in: PlatformUpdate):
    platform_obj = await platform_controller.get(id=platform_in.id)
    if platform_obj.custom_name == NATURE_CUSTOM_NAME:
        raise HTTPException(status_code=400, detail="自然流量渠道不允许编辑")
    if platform_in.custom_name == NATURE_CUSTOM_NAME:
        raise HTTPException(status_code=400, detail="nature 为系统保留标识")
    if await platform_controller.model.filter(custom_name=platform_in.custom_name).exclude(id=platform_in.id).exists():
        raise HTTPException(status_code=400, detail="自定义名称已存在")
    await platform_controller.update(id=platform_in.id, obj_in=platform_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除渠道")
async def delete_platform(id: int = Query(..., description="渠道ID")):
    platform_obj = await platform_controller.get(id=id)
    if platform_obj.custom_name == NATURE_CUSTOM_NAME:
        raise HTTPException(status_code=400, detail="自然流量渠道不允许删除")
    await platform_controller.remove(id=id)
    return Success(msg="Deleted Successfully")
