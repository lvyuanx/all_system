from .views import site_address_list_view, cur_site_options_view

apis = {
    "": [
        (
            "A0",
            "site_address_list",
            site_address_list_view.View,
            "查询站点地址列表",
        ),
        (
            "A1",
            "cur_site_options",
            cur_site_options_view.View,
            "查询当前用户所在的站点",
        ),
    ]
}
