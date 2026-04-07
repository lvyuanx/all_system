from client_mgmt.views import (
    mobile_client_address_list_view,
    mobile_client_list_view,
    mobile_client_info_view,
)

apis = {
    "client": [
        ("A0", "client_address_list/", mobile_client_address_list_view.View, "移动端客户地址列表"),
        ("A1", "list/", mobile_client_list_view.View, "移动端客户分页列表"),
        ("A2", "info/", mobile_client_info_view.View, "移动端客户详情"),
    ],
}
