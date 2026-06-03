from io import BytesIO

from fastapi import HTTPException
from openpyxl import Workbook
from tortoise.functions import Count

from app.core.crud import CRUDBase
from app.models.admin import Tag
from app.schemas.tags import TagCreate, TagImportItem, TagUpdate


class TagController(CRUDBase[Tag, TagCreate, TagUpdate]):
    def __init__(self):
        super().__init__(model=Tag)

    async def ensure_name_unique(self, name: str, exclude_id: int | None = None):
        query = self.model.filter(name=name)
        if exclude_id is not None:
            query = query.exclude(id=exclude_id)
        if await query.exists():
            raise HTTPException(status_code=400, detail="标签名称已存在")

    async def list_with_product_count(self, page: int, page_size: int, search, order: list[str]):
        query = self.model.filter(search).annotate(product_count=Count("products", distinct=True))
        total = await query.count()
        objs = await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)
        return total, objs

    async def create(self, obj_in: TagCreate):
        name = obj_in.get("name") if isinstance(obj_in, dict) else obj_in.name
        await self.ensure_name_unique(name)
        return await super().create(obj_in=obj_in)

    async def update(self, id: int, obj_in: TagUpdate):
        name = obj_in.get("name") if isinstance(obj_in, dict) else obj_in.name
        await self.ensure_name_unique(name, exclude_id=id)
        return await super().update(id=id, obj_in=obj_in)

    async def remove(self, id: int) -> None:
        tag = await self.get(id=id)
        if await tag.products.all().count():
            raise HTTPException(status_code=400, detail="标签已关联好物，无法删除")
        if await tag.hot_categories.all().count():
            raise HTTPException(status_code=400, detail="标签已关联热门分类，无法删除")
        await tag.delete()

    async def remove_many(self, ids: list[int]) -> int:
        normalized_ids = list(dict.fromkeys(ids))
        for item_id in normalized_ids:
            await self.remove(id=item_id)
        return len(normalized_ids)

    async def build_import_template(self) -> bytes:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "标签导入模板"
        worksheet.append(["标签名称", "备注", "检索次数", "排序", "是否启用"])
        worksheet.append(["示例标签", "这是一条示例备注", 0, 0, 1])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    async def import_items(self, items: list[TagImportItem]):
        created = 0
        for item in items:
            await self.ensure_name_unique(item.name)
            await super().create(obj_in=item.model_dump())
            created += 1
        return created


tag_controller = TagController()
