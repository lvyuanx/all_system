from pydantic import Field, BaseModel

class AddressLevelItemSchema(BaseModel):
    id: int = Field(description="主键")
    name: str = Field(description="名称")
    code: str = Field(description="代码")


class ImageSearchResultListItemSchema(BaseModel):
    stored_name: str = Field(description="图片名称")
    original_name: str = Field(description="原始图片名称")
    score: float = Field(description="相似度")

class ImageListSchema(BaseModel):
    total: int = Field(description="图片总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    results: list = Field(description="图片列表")