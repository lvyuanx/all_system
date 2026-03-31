from .views import mobile_login_view, mobile_logout_view, mobile_menu_view

apis = {
    "account": [
        ("A0", "login/", mobile_login_view.View, "移动端登录"),
        ("A1", "logout/", mobile_logout_view.View, "移动端退出登录"),
    ],
    "menu": [
        ("B0", "list/", mobile_menu_view.View, "查询移动端菜单"),
    ],
}
