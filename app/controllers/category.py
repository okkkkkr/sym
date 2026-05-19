from fastapi import HTTPException
from tortoise.transactions import atomic

from app.core.crud import CRUDBase
from app.models.admin import Brand, Category, Product, Tag
from app.schemas.categories import CategoryCreate, CategoryInheritResult, CategoryUpdate


class CategoryController(CRUDBase[Category, CategoryCreate, CategoryUpdate]):
    def __init__(self):
        super().__init__(model=Category)

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