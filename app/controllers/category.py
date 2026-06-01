from io import BytesIO

from fastapi import HTTPException
from openpyxl import Workbook
from tortoise.transactions import atomic

from app.core.crud import CRUDBase
from app.models.admin import Brand, Category, Product, Tag
from app.schemas.categories import CategoryCreate, CategoryImportItem, CategoryInheritResult, CategoryUpdate


class CategoryController(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self):
        super().__init__(model=Category)

    async def ensure_name_unique(self, name: str, exclude_id: int | None = None):
        query = self.model.filter(name=name)
        if exclude_id is not None:
            query = query.exclude(id=exclude_id)
        if await query.exists():
            raise HTTPException(status_code=400, detail="分类名称已存在")

    async def create(self, obj_in: CategoryCreate):
        name = obj_in.get("name") if isinstance(obj_in, dict) else obj_in.name
        await self.ensure_name_unique(name)
        return await super().create(obj_in=obj_in)

    async def update(self, id: int, obj_in: CategoryUpdate):
        name = obj_in.get("name") if isinstance(obj_in, dict) else obj_in.name
        await self.ensure_name_unique(name, exclude_id=id)
        return await super().update(id=id, obj_in=obj_in)

    async def build_import_template(self) -> bytes:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "分类导入模板"
        worksheet.append(["分类名称", "分类描述", "排序", "是否启用"])
        worksheet.append(["示例分类", "这是一条示例分类描述", 0, "是"])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    async def import_items(self, items: list[CategoryImportItem]):
        created = 0
        for item in items:
            await self.ensure_name_unique(item.name)
            await super().create(obj_in=item.model_dump())
            created += 1
        return created

    @atomic()
    async def inherit_content(self, source_id: int, target_id: int) -> CategoryInheritResult:
        if source_id == target_id:
            raise HTTPException(status_code=400, detail="source_id and target_id must be different")

        source = await self.get(id=source_id)
        target = await self.get(id=target_id)

        source_brand_ids = await Brand.filter(categories__id=source.id).distinct().values_list("id", flat=True)
        source_hot_brand_ids = await source.hot_brands.all().values_list("id", flat=True)
        source_hot_tag_ids = await source.hot_tags.all().values_list("id", flat=True)
        transferred_product_count = await Product.filter(category_id=source.id).count()

        if source_brand_ids:
            target_brand_ids = set(await Brand.filter(categories__id=target.id).distinct().values_list("id", flat=True))
            brand_ids_to_attach = [brand_id for brand_id in source_brand_ids if brand_id not in target_brand_ids]
            if brand_ids_to_attach:
                await target.brands.add(*await Brand.filter(id__in=brand_ids_to_attach))
            await source.brands.remove(*await Brand.filter(id__in=source_brand_ids))

        if source_hot_brand_ids:
            target_hot_brand_ids = set(await target.hot_brands.all().values_list("id", flat=True))
            hot_brand_ids_to_attach = [brand_id for brand_id in source_hot_brand_ids if brand_id not in target_hot_brand_ids]
            if hot_brand_ids_to_attach:
                await target.hot_brands.add(*await Brand.filter(id__in=hot_brand_ids_to_attach))
            await source.hot_brands.clear()

        if source_hot_tag_ids:
            target_hot_tag_ids = set(await target.hot_tags.all().values_list("id", flat=True))
            tag_ids_to_attach = [tag_id for tag_id in source_hot_tag_ids if tag_id not in target_hot_tag_ids]
            if tag_ids_to_attach:
                await target.hot_tags.add(*await Tag.filter(id__in=tag_ids_to_attach))
            await source.hot_tags.clear()

        if transferred_product_count:
            await Product.filter(category_id=source.id).update(category_id=target.id)

        return CategoryInheritResult(
            source_id=source.id,
            target_id=target.id,
            transferred_brand_count=len(source_brand_ids),
            transferred_hot_brand_count=len(source_hot_brand_ids),
            transferred_hot_tag_count=len(source_hot_tag_ids),
            transferred_product_count=transferred_product_count,
        )


category_controller = CategoryController()
