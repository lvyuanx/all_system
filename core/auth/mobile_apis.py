from .views import mobile_login_view

apis = {
    "account": [
        ("A0", "login/", mobile_login_view.View, "移动端登录"),
    ],
}
