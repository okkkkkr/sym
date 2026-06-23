from pydantic import BaseModel, Field


class VideoResourceOut(BaseModel):
    id: int
    status: str = Field(..., description="处理状态")
    storage_provider: str = Field("", description="存储驱动")
    storage_key: str = Field("", description="对象 Key")
    public_url: str = Field("", description="公开访问地址")
    original_size: int = Field(0, description="原始文件大小")
    compressed_size: int | None = Field(None, description="压缩后文件大小")
    error_message: str = Field("", description="错误信息")
    updated_at: str | None = Field(None, description="更新时间")


class VideoUploadAcceptedOut(VideoResourceOut):
    media_type: str = Field("video", description="媒体类型")
    delete_token: str = Field("", description="删除令牌")
