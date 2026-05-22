from io import BytesIO

from fastapi import HTTPException
from openpyxl import Workbook
from tortoise.transactions import atomic

from app.core.crud import CRUDBase
from app.models.admin import Category
from app.models.admin import Brand
from app.models.admin import Product
from app.schemas.brands import BrandCreate, BrandImportItem, BrandInheritResult, BrandUpdate


class BrandController(CRUDBase[Brand, BrandCreate, BrandUpdate]):
    def __init__(self):
        super().__init__(model=Brand)

    async def _get_categories(self, category_ids: list[int]) -> list[Category]:
        if not category_ids:
            return []
        return await Category.filter(id__in=category_ids)

    async def create_with_categories(self, obj_in: BrandCreate) -> Brand:
        brand = await self.create(obj_in=obj_in.model_dump(exclude={"category_ids"}))
        if obj_in.category_ids:
            await brand.categories.add(*await self._get_categories(obj_in.category_ids))
        return brand

    async def update_with_categories(self, id: int, obj_in: BrandUpdate) -> Brand:
        brand = await self.update(id=id, obj_in=obj_in.model_dump(exclude={"id", "category_ids"}))
        await brand.categories.clear()
        if obj_in.category_ids:
            await brand.categories.add(*await self._get_categories(obj_in.category_ids))
        return brand

    async def get_category_ids(self, brand: Brand) -> list[int]:
        return [category.id for category in await brand.categories.all()]

    async def ensure_name_unique(self, name: str):
        if await self.model.filter(name=name).exists():
            raise HTTPException(status_code=400, detail="品牌名称已存在")

    async def build_import_template(self) -> bytes:
        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "品牌导入模板"
        worksheet.append(["品牌名称", "所属分类", "品牌描述", "检索次数", "排序", "是否启用"])
        worksheet.append(["示例品牌", "示例分类A;示例分类B", "这是一条示例品牌描述", 0, 0, "是"])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    async def import_items(self, items: list[BrandImportItem]):
        created = 0
        for item in items:
            await self.ensure_name_unique(item.name)
            await self.create_with_categories(BrandCreate(**item.model_dump()))
            created += 1
        return created

    @atomic()
    async def inherit_content(self, source_id: int, target_id: int) -> BrandInheritResult:
        if source_id == target_id:
            raise HTTPException(status_code=400, detail="source_id and target_id must be different")

        source = await self.get(id=source_id)
        target = await self.get(id=target_id)
        transferred_product_count = await Product.filter(brand_id=source.id).count()
        if transferred_product_count:
            await Product.filter(brand_id=source.id).update(brand_id=target.id)

        return BrandInheritResult(
            source_id=source.id,
            target_id=target.id,
            transferred_product_count=transferred_product_count,
        )


brand_controller = BrandController()