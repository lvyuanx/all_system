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


class LoginRequestSchema(BaseModel):
    username: str = Field(..., description="用户名/手机号/工号")
    password: str = Field(..., description="密码")


class LoginResponseSchema(BaseModel):
    uid: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    full_name: str | None = Field(default=None, description="姓名")
    phone: str | None = Field(default=None, description="手机号")
    avatar: str | None = Field(default=None, description="头像URL")
    date_joined: str | None = Field(default=None, description="创建时间")
    is_superuser: bool = Field(default=False, description="是否是超级管理员")
    channel: str = Field(..., description="登录通道：admin/mobile")
    token_tag: str = Field(..., description="Token字段名")
    token_origin: str | None = Field(default=None, description="兼容字段，主来源")
    token_read_from: list[str] = Field(default_factory=list, description="Token读取来源")
    token_write_to: list[str] = Field(default_factory=list, description="Token写入来源")
    token_expire: int = Field(..., description="Token过期秒数")
    token: str | None = Field(default=None, description="登录返回Token")


class MobileMenuItemSchema(BaseModel):
    id: int = Field(..., description="菜单ID")
    name: str = Field(..., description="菜单名称")
    icon: str | None = Field(default=None, description="图标")
    url: str | None = Field(default=None, description="菜单链接")
    path: str | None = Field(default=None, description="菜单路径")
    depath: int = Field(..., description="路径深度")
    sort_no: int = Field(default=0, description="排序")
    has_children: bool = Field(default=False, description="是否有子菜单")


class MobileProfileSchema(BaseModel):
    uid: int = Field(..., description="用户ID")
    username: str = Field(..., description="用户名")
    first_name: str | None = Field(default=None, description="名")
    last_name: str | None = Field(default=None, description="姓")
    full_name: str | None = Field(default=None, description="姓名")
    email: str | None = Field(default=None, description="邮箱")
    phone: str | None = Field(default=None, description="手机号")
    sex: str | None = Field(default=None, description="性别：M/F/U")
    age: int | None = Field(default=None, description="年龄")
    avatar: str | None = Field(default=None, description="头像URL")


class MobileProfileUpdateSchema(BaseModel):
    username: str | None = Field(default=None, description="用户名")
    first_name: str | None = Field(default=None, description="名")
    last_name: str | None = Field(default=None, description="姓")
    email: str | None = Field(default=None, description="邮箱")
    phone: str | None = Field(default=None, description="手机号")
    sex: str | None = Field(default=None, description="性别：M/F/U")
    age: int | None = Field(default=None, description="年龄")


class MobileChangePasswordSchema(BaseModel):
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., description="新密码")

