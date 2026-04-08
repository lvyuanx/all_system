from pydantic import BaseModel, Field


class PatternListItemSchema(BaseModel):

    pattern_id: int = Field(..., description="版式ID")
    main_image: str = Field(..., description="主图")
    pattern_code: str = Field(..., description="版号")
    pattern_memo: str | None = Field(None, description="备注")
    tags: list[str] = Field(default_factory=list, description="标签")


class EchoImageDataSchema(BaseModel):
    rid: int = Field(..., description="图片id")
    name: str = Field(..., description="图片名称")
    url: str = Field(..., description="图片地址")


class PatternInfoSchema(BaseModel):

    id: int = Field(..., description="版式ID")
    code: str = Field(..., description="版号")
    memo: str | None = Field(None, description="备注")
    is_active: bool = Field(..., description="是否启用")
    tags: list[str] = Field(..., description="标签")
    main_image: EchoImageDataSchema = Field(..., description="主图")
    images: list[EchoImageDataSchema] = Field(..., description="辅图")
