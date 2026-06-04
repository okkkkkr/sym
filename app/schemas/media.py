from pydantic import BaseModel, Field, model_validator


class MediaDeleteIn(BaseModel):
    key: str | None = Field(default=None, max_length=500, description="待删除对象 Key")
    keys: list[str] = Field(default_factory=list, description="待删除对象 Key 列表")

    @model_validator(mode="after")
    def validate_keys(self):
        normalized_keys = []
        if self.key is not None:
            normalized_keys.append(str(self.key).strip())
        normalized_keys.extend(str(item).strip() for item in self.keys)
        self.keys = list(dict.fromkeys(item for item in normalized_keys if item))
        if not self.keys:
            raise ValueError("key or keys is required")
        return self
