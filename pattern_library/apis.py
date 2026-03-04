from .views import pattern_list_view, pattern_add_view

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
        )
    ]
}
