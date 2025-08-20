from pydantic import Field, BaseModel
from ninja import ModelSchema
from ..models import SimpleuiMenus


class PermPackItemSchema(BaseModel):
    pack_name: str = Field(description="权限包名称")
    pack_code: str = Field(description="权限包编码")


class GroupCreateSchema(BaseModel):
    name: str = Field(description="权限组名称")
    packs: list[str] = Field(description="权限包列表")
    


class MenuItemCreateSchema(ModelSchema):
    
    class Config:
        model = SimpleuiMenus
        model_exclude  = ("id",)