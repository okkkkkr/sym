from typing import Any, Dict, Generic, List, NewType, Tuple, Type, TypeVar, Union

from pydantic import BaseModel
from tortoise.expressions import Case, Q, When
from tortoise.models import Model

Total = NewType("Total", int)
ModelType = TypeVar("ModelType", bound=Model)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    @staticmethod
    def build_order(
        default_order: list[str],
        sort_field: str | None = None,
        sort_order: str | None = None,
        allowed_fields: set[str] | None = None,
    ) -> list[str]:
        if not sort_field or not allowed_fields or sort_field not in allowed_fields:
            return default_order

        normalized_sort_order = str(sort_order or "desc").lower()
        prefix = "" if normalized_sort_order == "asc" else "-"
        requested_order = f"{prefix}{sort_field}"
        fallback_order = [item for item in default_order if item.lstrip("-") != sort_field]
        return [requested_order, *fallback_order]

    @staticmethod
    def build_nullable_field_order(
        field_name: str,
        fallback_order: list[str],
        sort_order: str | None = None,
    ) -> tuple[dict[str, Any], list[str]]:
        normalized_sort_order = str(sort_order or "asc").lower()
        prefix = "" if normalized_sort_order == "asc" else "-"
        annotation_name = f"__{field_name}_null_rank"
        filtered_fallback_order = [
            item
            for item in fallback_order
            if item.lstrip("-") not in {field_name, annotation_name}
        ]
        return (
            {
                annotation_name: Case(
                    When(**{f"{field_name}__isnull": True}, then=1),
                    default=0,
                )
            },
            [annotation_name, f"{prefix}{field_name}", *filtered_fallback_order],
        )

    async def get(self, id: int) -> ModelType:
        return await self.model.get(id=id)

    async def list(
        self,
        page: int,
        page_size: int,
        search: Q = Q(),
        order: list = [],
        annotations: dict[str, Any] | None = None,
    ) -> Tuple[Total, List[ModelType]]:
        query = self.model.filter(search)
        if annotations:
            query = query.annotate(**annotations)
        return await query.count(), await query.offset((page - 1) * page_size).limit(page_size).order_by(*order)

    async def create(self, obj_in: CreateSchemaType) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump()
        obj = self.model(**obj_dict)
        await obj.save()
        return obj

    async def update(self, id: int, obj_in: Union[UpdateSchemaType, Dict[str, Any]]) -> ModelType:
        if isinstance(obj_in, Dict):
            obj_dict = obj_in
        else:
            obj_dict = obj_in.model_dump(exclude_unset=True, exclude={"id"})
        obj = await self.get(id=id)
        obj = obj.update_from_dict(obj_dict)
        await obj.save()
        return obj

    async def remove(self, id: int) -> None:
        obj = await self.get(id=id)
        await obj.delete()

    async def remove_many(self, ids: List[int]) -> int:
        normalized_ids = list(dict.fromkeys(ids))
        if not normalized_ids:
            return 0
        deleted_count = 0
        for item_id in normalized_ids:
            await self.remove(id=item_id)
            deleted_count += 1
        return deleted_count
