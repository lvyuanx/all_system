from .views import pattern_list_view, pattern_add_view, pattern_info_view, pattern_change_view

apis = {
    "": [
        (
            "A0",
            "pattern_list",
            pattern_list_view.View,
            "查询版式列表",
        ),
        (
            "A1",
            "pattern_add",
            pattern_add_view.View,
            "查询版式列表",
        ),
        (
            "A2",
            "pattern_info",
            pattern_info_view.View,
            "查询版式详情",
        ),
        (
            "A3",
            "pattern_change",
            pattern_change_view.View,
            "更新版式信息",
        )
    ]
}
