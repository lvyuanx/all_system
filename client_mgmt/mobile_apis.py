from client_mgmt.views import mobile_client_address_list_view

apis = {
    "client": [
        ("A0", "client_address_list/", mobile_client_address_list_view.View, "移动端客户地址列表"),
    ],
}
