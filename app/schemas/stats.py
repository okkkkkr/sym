from pydantic import BaseModel, Field, field_validator


class TrackProductClickIn(BaseModel):
    product_id: int = Field(..., ge=1, description="好物ID")


class TrackBrandSearchIn(BaseModel):
    brand_ids: list[int] = Field(default_factory=list, description="品牌ID列表")

    @field_validator("brand_ids")
    @classmethod
    def normalize_brand_ids(cls, value: list[int]):
        brand_ids = []
        for brand_id in value:
            if brand_id <= 0:
                continue
            if brand_id not in brand_ids:
                brand_ids.append(brand_id)
        return brand_ids


class TrackSiteVisitIn(BaseModel):
    visitor_id: str = Field(..., min_length=8, max_length=64, description="访客标识")
    region: str = Field(default="", max_length=100, description="所属区域")
    path: str = Field(default="", max_length=255, description="访问路径")

    @field_validator("visitor_id")
    @classmethod
    def normalize_visitor_id(cls, value: str):
        return value.strip()

    @field_validator("region")
    @classmethod
    def normalize_region(cls, value: str):
        return value.strip()[:100]

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str):
        return value.strip()[:255]


class TrackBannerClickIn(BaseModel):
    banner_id: int = Field(..., ge=1, description="横幅ID")