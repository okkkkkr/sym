from fastapi import APIRouter, HTTPException, Query
from tortoise.expressions import Q

from app.controllers.contact import contact_controller
from app.models.admin import Contact
from app.schemas.base import Success, SuccessExtra
from app.schemas.contacts import ContactCreate, ContactUpdate

router = APIRouter()


@router.get("/list", summary="查看联系方式列表")
async def list_contact(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="关键字"),
    contact_type: str = Query("", description="联系方式类型"),
    is_active: bool | None = Query(None, description="是否启用"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q = Q(is_deleted=False)
    if keyword:
        q &= Q(platform__contains=keyword) | Q(display_name__contains=keyword) | Q(contact_value__contains=keyword)
    if contact_type:
        q &= Q(contact_type=contact_type)
    if is_active is not None:
        q &= Q(is_active=is_active)
    order = contact_controller.build_order(
        default_order=["-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"updated_at", "platform", "display_name", "order", "is_active"},
    )
    total, contact_objs = await contact_controller.list(page=page, page_size=page_size, search=q, order=order)
    data = [await obj.to_dict() for obj in contact_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看联系方式")
async def get_contact(id: int = Query(..., description="联系方式ID")):
    contact_obj = await Contact.filter(id=id, is_deleted=False).first()
    if not contact_obj:
        raise HTTPException(status_code=404, detail="Contact not found")
    return Success(data=await contact_obj.to_dict())


@router.post("/create", summary="创建联系方式")
async def create_contact(contact_in: ContactCreate):
    await contact_controller.create(obj_in=contact_in)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新联系方式")
async def update_contact(contact_in: ContactUpdate):
    await contact_controller.update(id=contact_in.id, obj_in=contact_in)
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除联系方式")
async def delete_contact(id: int = Query(..., description="联系方式ID")):
    await contact_controller.remove(id=id)
    return Success(msg="Deleted Successfully")
