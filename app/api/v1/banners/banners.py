from fastapi import APIRouter, Query
from tortoise.expressions import Q

from app.controllers.banner import banner_controller
from app.schemas.banners import BannerCreate, BannerUpdate
from app.schemas.base import Success, SuccessExtra

router = APIRouter()


@router.get("/list", summary="查看横幅列表")
async def list_banner(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    content: str = Query("", description="横幅内容"),
    note: str = Query("", description="活动备注"),
    is_active: bool | None = Query(None, description="是否启用"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q = Q()
    if content:
        q &= Q(content__contains=content)
    if note:
        q &= Q(note__contains=note)
    if is_active is not None:
        q &= Q(is_active=is_active)
    order = banner_controller.build_order(
        default_order=["-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"updated_at", "content", "priority", "click_count", "is_active"},
    )
    total, banner_objs = await banner_controller.list(page=page, page_size=page_size, search=q, order=order)
    return SuccessExtra(data=[await obj.to_dict() for obj in banner_objs], total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看横幅")
async def get_banner(id: int = Query(..., description="横幅ID")):
    banner_obj = await banner_controller.get(id=id)
    return Success(data=await banner_obj.to_dict())


@router.post("/create", summary="创建横幅")
async def create_banner(banner_in: BannerCreate):
    await banner_controller.create(obj_in=banner_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新横幅")
async def update_banner(banner_in: BannerUpdate):
    await banner_controller.update(id=banner_in.id, obj_in=banner_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除横幅")
async def delete_banner(id: int = Query(..., description="横幅ID")):
    await banner_controller.remove(id=id)
    return Success(msg="Deleted Successfully")