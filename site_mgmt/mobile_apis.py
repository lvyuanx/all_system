from site_mgmt.views import cur_site_options_view, mobile_site_address_list_view

apis = {
    "site": [
        ("A0", "site_options/", cur_site_options_view.View, "移动端站点信息"),
        ("A1", "site_address_list/", mobile_site_address_list_view.View, "移动端站点地址列表"),
    ],
}
