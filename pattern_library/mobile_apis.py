from .views import (
    mobile_pattern_list_view,
    mobile_pattern_info_view,
    mobile_pattern_deactivate_view,
    mobile_pattern_activate_view,
    mobile_pattern_add_view,
    mobile_pattern_change_view,
    pattern_category_list_view,
    pattern_code_preview_view,
)

apis = {
    "pattern": [
        ("A0", "list/", mobile_pattern_list_view.View, "移动端分页查询版式"),
        ("A1", "info/", mobile_pattern_info_view.View, "移动端查询版式详情"),
        ("A2", "deactivate/", mobile_pattern_deactivate_view.View, "移动端下架版式"),
        ("A3", "change/", mobile_pattern_change_view.View, "移动端编辑版式"),
        ("A4", "activate/", mobile_pattern_activate_view.View, "mobile activate pattern"),
        ("A5", "add/", mobile_pattern_add_view.View, "mobile add pattern"),
        ("A6", "categories/", pattern_category_list_view.View, "mobile list pattern categories"),
        ("A7", "code_preview/", pattern_code_preview_view.View, "mobile preview pattern code"),
    ],
}
