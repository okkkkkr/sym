from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator
from fastapi.responses import JSONResponse


class Success(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: Optional[str] = "OK",
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class Fail(JSONResponse):
    def __init__(
        self,
        code: int = 400,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        **kwargs,
    ):
        content = {"code": code, "msg": msg, "data": data}
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class SuccessExtra(JSONResponse):
    def __init__(
        self,
        code: int = 200,
        msg: Optional[str] = None,
        data: Optional[Any] = None,
        total: int = 0,
        page: int = 1,
        page_size: int = 20,
        **kwargs,
    ):
        content = {
            "code": code,
            "msg": msg,
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
        content.update(kwargs)
        super().__init__(content=content, status_code=code)


class DeleteIdsIn(BaseModel):
    scope: Literal["selected", "filtered", "all"] = "selected"
    id: int | None = None
    ids: list[int] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_ids(self):
        normalized_ids = []
        if self.id is not None:
            normalized_ids.append(self.id)
        normalized_ids.extend(self.ids)
        normalized_ids = list(dict.fromkeys(item for item in normalized_ids if item is not None))
        if self.scope == "selected" and not normalized_ids:
            raise ValueError("id or ids is required")
        self.ids = normalized_ids
        return self
