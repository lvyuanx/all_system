from .views import client_address_list

apis = {
    "": [
        (
            "A0",
            "client_address_list",
            client_address_list.View,
            "查询客户地址列表",
        )
    ]
}
