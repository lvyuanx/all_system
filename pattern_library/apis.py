from .views import pattern_list_view

apis = {
    "": [
        (
            "A0",
            "pattern_list",
            pattern_list_view.View,
            "查询版式列表",
        )
    ]
}
