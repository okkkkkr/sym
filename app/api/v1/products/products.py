from fastapi import APIRouter, Body, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from tortoise.expressions import Q

from app.controllers.brand import brand_controller
from app.controllers.category import category_controller
from app.controllers.product import product_controller
from app.controllers.tag import tag_controller
from app.core.dependency import DependAuth
from app.models import User
from app.services.media_cleanup import delete_media_keys, diff_removed_media_keys, normalize_media_keys
from app.services.media_storage import media_storage_service
from app.settings import settings
from app.schemas.base import DeleteIdsIn, Success, SuccessExtra
from app.schemas.products import ProductCreate, ProductMediaUploadTokenIn, ProductUpdate
from app.utils.excel_export import build_xlsx_content

router = APIRouter()


@router.post("/media/upload-token", summary="获取好物媒体上传凭证")
async def get_product_media_upload_token(payload: ProductMediaUploadTokenIn, current_user: User = DependAuth):
    _ = current_user
    _ = payload
    raise HTTPException(status_code=410, detail="上传凭证接口已废弃，请使用后端中转上传接口")


@router.post("/media/upload", summary="上传好物媒体文件")
async def upload_product_media(
    media_type: str = Query(..., description="媒体类型: cover/image/video"),
    file: UploadFile = File(...),
    current_user: User = DependAuth,
):
    _ = current_user
    return Success(data=await media_storage_service.upload(file, media_type))


async def serialize_product_payload(product_obj):
    product_data = await product_obj.to_dict()
    product_data["cover_image_key"] = product_data.get("cover_image_key") or ""
    product_data["image_keys"] = list(product_data.get("image_keys") or [])
    product_data["video_keys"] = list(product_data.get("video_keys") or [])
    product_data["cover_image_url"] = media_storage_service.serialize_object_key(product_data.get("cover_image_key"))
    product_data["image_urls"] = [
        media_storage_service.serialize_object_key(item) for item in product_data.get("image_keys") or []
    ]
    product_data["video_urls"] = [
        media_storage_service.serialize_object_key(item) for item in product_data.get("video_keys") or []
    ]
    product_data["product_code_custom"] = product_controller.extract_product_code_custom(
        product_data.get("product_code")
    )
    tag_sort_annotations, tag_sort_order = tag_controller.build_nullable_field_order("sort", ["-updated_at", "-id"])
    product_data["tags"] = [
        {"id": tag.id, "name": tag.name}
        for tag in await product_obj.tags.all().annotate(**tag_sort_annotations).order_by(*tag_sort_order)
    ]
    product_data["tag_ids"] = [tag["id"] for tag in product_data["tags"]]
    return product_data


def parse_optional_bool(value) -> bool | None:
    if value in (None, "", "all"):
        return None
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    return None


def parse_optional_int(value) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def build_product_search(
    keyword: str = "",
    category_id=None,
    brand_id=None,
    tag_id=None,
    status=None,
) -> tuple[Q, bool]:
    q = Q()
    has_filters = False
    normalized_keyword = str(keyword or "").strip()
    normalized_category_id = parse_optional_int(category_id)
    normalized_brand_id = parse_optional_int(brand_id)
    normalized_tag_id = parse_optional_int(tag_id)
    normalized_status = parse_optional_bool(status)

    if normalized_keyword:
        q &= Q(name__contains=normalized_keyword)
        has_filters = True
    if normalized_category_id is not None:
        q &= Q(category_id=normalized_category_id)
        has_filters = True
    if normalized_brand_id is not None:
        q &= Q(brand_id=normalized_brand_id)
        has_filters = True
    if normalized_tag_id is not None:
        q &= Q(tags__id=normalized_tag_id)
        has_filters = True
    if normalized_status is not None:
        q &= Q(status=normalized_status)
        has_filters = True

    return q, has_filters


async def resolve_product_ids(payload: DeleteIdsIn) -> list[int]:
    if payload.scope == "selected":
        return payload.ids

    if payload.scope == "filtered":
        search, has_filters = build_product_search(
            keyword=payload.filters.get("keyword", ""),
            category_id=payload.filters.get("category_id"),
            brand_id=payload.filters.get("brand_id"),
            tag_id=payload.filters.get("tag_id"),
            status=payload.filters.get("status"),
        )
        if not has_filters:
            return []
        return list(await product_controller.model.filter(search).distinct().values_list("id", flat=True))

    return list(await product_controller.model.all().values_list("id", flat=True))


@router.get("/list", summary="查看好物列表")
async def list_product(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    keyword: str = Query("", description="关键字"),
    category_id: int | None = Query(None, description="类目ID"),
    brand_id: int | None = Query(None, description="品牌ID"),
    tag_id: int | None = Query(None, description="标签ID"),
    status: bool | None = Query(None, description="是否上架"),
    sort_field: str | None = Query(None, description="排序字段"),
    sort_order: str | None = Query(None, description="排序方向 asc/desc"),
):
    q, _ = build_product_search(
        keyword=keyword,
        category_id=category_id,
        brand_id=brand_id,
        tag_id=tag_id,
        status=status,
    )
    annotations = None
    order = product_controller.build_order(
        default_order=["-updated_at", "-id"],
        sort_field=sort_field,
        sort_order=sort_order,
        allowed_fields={"updated_at", "name", "order", "click_count", "status"},
    )
    if sort_field == "order":
        annotations, order = product_controller.build_nullable_field_order("order", ["-updated_at", "-id"], sort_order)
    total, product_objs = await product_controller.list(
        page=page,
        page_size=page_size,
        search=q,
        order=order,
        annotations=annotations,
    )
    data = []
    for obj in product_objs:
        item = await serialize_product_payload(obj)
        category = await category_controller.get(id=item["category_id"])
        brand = await brand_controller.get(id=item["brand_id"])
        item["category"] = await category.to_dict()
        item["brand"] = await brand.to_dict()
        item["category_name"] = category.name
        item["brand_name"] = brand.name
        data.append(item)
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看好物")
async def get_product(id: int = Query(..., description="好物ID")):
    product_obj = await product_controller.get(id=id)
    data = await serialize_product_payload(product_obj)
    category = await category_controller.get(id=data["category_id"])
    brand = await brand_controller.get(id=data["brand_id"])
    data["category"] = await category.to_dict()
    data["brand"] = await brand.to_dict()
    data["category_name"] = category.name
    data["brand_name"] = brand.name
    return Success(data=data)


@router.post("/create", summary="创建好物")
async def create_product(product_in: ProductCreate):
    await product_controller.ensure_relations(product_in.category_id, product_in.brand_id)
    tag_ids = await product_controller.ensure_tag_ids_exist(product_in.tag_ids)
    payload = product_in.model_dump(exclude={"product_code_custom", "tag_ids"})
    payload["image_keys"] = product_controller.normalize_media_keys(payload.get("image_keys") or [])
    payload["product_code"] = await product_controller.build_product_code(product_in.product_code_custom)
    await product_controller.create_with_tags(obj_in=payload, tag_ids=tag_ids)
    return Success(msg="Created Successfully")


@router.post("/update", summary="更新好物")
async def update_product(product_in: ProductUpdate):
    await product_controller.ensure_relations(product_in.category_id, product_in.brand_id)
    tag_ids = await product_controller.ensure_tag_ids_exist(product_in.tag_ids)
    current_product = await product_controller.get(id=product_in.id)
    previous_media_keys = normalize_media_keys(
        [current_product.cover_image_key, *(current_product.image_keys or []), *(current_product.video_keys or [])]
    )
    payload = product_in.model_dump(exclude={"id", "product_code_custom", "tag_ids"})
    payload["image_keys"] = product_controller.normalize_media_keys(payload.get("image_keys") or [])
    payload["product_code"] = await product_controller.build_product_code(
        product_in.product_code_custom,
        current_code=current_product.product_code,
    )
    await product_controller.update_with_tags(id=product_in.id, obj_in=payload, tag_ids=tag_ids)
    await delete_media_keys(
        diff_removed_media_keys(
            previous_media_keys,
            [payload.get("cover_image_key"), *(payload.get("image_keys") or []), *(payload.get("video_keys") or [])],
        )
    )
    return Success(msg="Updated Successfully")


@router.delete("/delete", summary="删除好物")
async def delete_product(payload: DeleteIdsIn = Body(...)):
    ids = await resolve_product_ids(payload)
    media_keys = normalize_media_keys(
        key
        for product in await product_controller.model.filter(id__in=ids).values(
            "cover_image_key", "image_keys", "video_keys"
        )
        for key in [
            product.get("cover_image_key"),
            *(product.get("image_keys") or []),
            *(product.get("video_keys") or []),
        ]
    )
    deleted_count = await product_controller.remove_many(ids=ids)
    await delete_media_keys(media_keys)
    return Success(msg="Deleted Successfully", data={"deleted": deleted_count})


@router.post("/export", summary="批量导出好物")
async def export_product(payload: DeleteIdsIn = Body(...)):
    ids = await resolve_product_ids(payload)
    order_annotations, export_order = product_controller.build_nullable_field_order("order", ["-updated_at", "-id"])
    product_objs = (
        await product_controller.model.filter(id__in=ids)
        .distinct()
        .annotate(**order_annotations)
        .order_by(*export_order)
    )

    category_ids = list({product.category_id for product in product_objs})
    brand_ids = list({product.brand_id for product in product_objs})
    category_map = {
        item["id"]: item["name"]
        for item in await category_controller.model.filter(id__in=category_ids).values("id", "name")
    }
    brand_map = {
        item["id"]: item["name"] for item in await brand_controller.model.filter(id__in=brand_ids).values("id", "name")
    }

    rows = []
    for product_obj in product_objs:
        item = await serialize_product_payload(product_obj)
        rows.append(
            [
                item.get("name") or "",
                item.get("product_code") or "",
                brand_map.get(item.get("brand_id"), ""),
                category_map.get(item.get("category_id"), ""),
                "\n".join(tag.get("name") or "" for tag in item.get("tags") or []),
                item.get("click_count") or 0,
                "上架" if item.get("status") else "下架",
                item.get("cover_image_url") or "",
                item.get("updated_at") or "",
                item.get("desc") or "",
            ]
        )

    content = build_xlsx_content(
        sheet_title="好物导出",
        headers=[
            "好物名称",
            "好物识别码",
            "所属品牌",
            "所属分类",
            "关联标签",
            "点击量",
            "上架状态",
            "封面图",
            "更新时间",
            "好物简介",
        ],
        rows=rows,
    )
    filename = f"product-export-{payload.scope}-{settings.VERSION}.xlsx"
    return StreamingResponse(
        iter([content]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
