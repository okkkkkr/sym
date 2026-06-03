import secrets
import string
import unicodedata
from datetime import datetime

from fastapi import HTTPException
from tortoise.exceptions import IntegrityError

from app.core.crud import CRUDBase
from app.models.admin import Product
from app.models.admin import Tag
from app.schemas.products import ProductCreate, ProductUpdate

from .brand import brand_controller
from .category import category_controller


class ProductController(CRUDBase[Product, ProductCreate, ProductUpdate]):
    def __init__(self):
        super().__init__(model=Product)

    @staticmethod
    def extract_product_code_custom(product_code: str | None) -> str:
        if not product_code:
            return ""
        prefix, _, _ = product_code.partition("-")
        if len(prefix) <= 4:
            return ""
        return prefix[4:]

    @staticmethod
    def _random_suffix(length: int = 8) -> str:
        alphabet = string.ascii_lowercase + string.digits
        return "".join(secrets.choice(alphabet) for _ in range(length))

    async def build_product_code(self, custom_value: str | None, current_code: str | None = None) -> str | None:
        normalized_custom = str(custom_value or "").strip()
        if not normalized_custom:
            return current_code
        if not normalized_custom.isdigit():
            raise HTTPException(status_code=400, detail="好物识别码仅支持数字")

        year = datetime.now().year
        prefix = f"{year}{normalized_custom}"
        if current_code and current_code.partition("-")[0] == prefix:
            return current_code
        for _ in range(10):
            candidate = f"{prefix}-{self._random_suffix()}"
            exists = await self.model.filter(product_code=candidate).exists()
            if not exists or candidate == current_code:
                return candidate

        raise HTTPException(status_code=500, detail="failed to generate product_code")

    async def _get_tags(self, tag_ids: list[int]) -> list[Tag]:
        if not tag_ids:
            return []
        return await Tag.filter(id__in=tag_ids)

    async def ensure_tag_ids_exist(self, tag_ids: list[int]) -> list[int]:
        normalized_tag_ids = list(dict.fromkeys(tag_ids))
        if not normalized_tag_ids:
            return []

        found_count = await Tag.filter(id__in=normalized_tag_ids).count()
        if found_count != len(normalized_tag_ids):
            raise HTTPException(status_code=400, detail="tag_ids contains invalid tag")

        return normalized_tag_ids

    @staticmethod
    def normalize_name(name: str) -> str:
        return unicodedata.normalize("NFKC", str(name or "").strip())

    async def ensure_name_unique(self, name: str, exclude_id: int | None = None) -> None:
        normalized_name = self.normalize_name(name)
        if not normalized_name:
            return

        for item_id, item_name in await self.model.all().values_list("id", "name"):
            if exclude_id is not None and item_id == exclude_id:
                continue
            if self.normalize_name(item_name) == normalized_name:
                raise HTTPException(status_code=400, detail="好物名称已存在")

    async def create_with_tags(self, obj_in: dict, tag_ids: list[int]) -> Product:
        await self.ensure_name_unique(obj_in.get("name"))
        try:
            product = await self.create(obj_in=obj_in)
        except IntegrityError as exc:
            raise HTTPException(status_code=400, detail="好物名称已存在") from exc
        if tag_ids:
            await product.tags.add(*await self._get_tags(tag_ids))
        return product

    async def update_with_tags(self, id: int, obj_in: dict, tag_ids: list[int]) -> Product:
        await self.ensure_name_unique(obj_in.get("name"), exclude_id=id)
        try:
            product = await self.update(id=id, obj_in=obj_in)
        except IntegrityError as exc:
            raise HTTPException(status_code=400, detail="好物名称已存在") from exc
        await product.tags.clear()
        if tag_ids:
            await product.tags.add(*await self._get_tags(tag_ids))
        return product

    async def ensure_relations(self, category_id: int, brand_id: int):
        category = await category_controller.get(id=category_id)
        brand = await brand_controller.get(id=brand_id)
        category_ids = await brand_controller.get_category_ids(brand)
        if category.id not in category_ids:
            raise HTTPException(status_code=400, detail="brand_id does not belong to the selected category")
        return category, brand


product_controller = ProductController()
