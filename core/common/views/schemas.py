from pydantic import Field, BaseModel

class AddressLevelItemSchema(BaseModel):
    id: int = Field(description="主键")
    name: str = Field(description="名称")
    code: str = Field(description="代码")