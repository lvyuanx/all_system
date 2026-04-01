from .views import mobile_staff_info_view

apis = {
    "staff": [
        ("A0", "info/", mobile_staff_info_view.View, "移动端员工信息"),
    ],
}
