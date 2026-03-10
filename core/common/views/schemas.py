from pydantic import Field, BaseModel

class AddressLevelItemSchema(BaseModel):
    id: int = Field(description="主键")
    name: str = Field(description="名称")
    code: str = Field(description="代码")


class ImageResultListItemSchema(BaseModel):
    stored_name: str = Field(description="图片名称")
    original_name: str = Field(description="原始图片名称")
    upload_time: str = Field(description="时间")
    group: str = Field(description="图库名称")
    url: str = Field(description="图片地址")

class ImageSearchResultListItemSchema(ImageResultListItemSchema):
    score: float = Field(description="相似度")

class ImageListSchema(BaseModel):
    total: int = Field(description="图片总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    results: list = Field(description="图片列表")