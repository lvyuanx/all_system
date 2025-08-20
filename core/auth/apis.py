from .views.perm_pack import pack_all_view, pack_list_by_group_view
from .views.group import group_create_view, group_update_view

apis = {
    "prem": [
        ("A0", "pack/all/", pack_all_view.View, "查询所有权限"),
        ("A1", "pack/list_by_group/", pack_list_by_group_view.View, "查询角色的权限包"),
    ],
    "group": [
        ("B1", "create/", group_create_view.View, "创建角色"),
        ("B2", "update/", group_update_view.View, "编辑角色"),
    ],
    "menu": [
    ],
}