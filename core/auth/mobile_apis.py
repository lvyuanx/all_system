from .views import (
    mobile_login_view,
    mobile_logout_view,
    mobile_menu_view,
    mobile_profile_view,
    mobile_profile_update_view,
    mobile_change_password_view,
)

apis = {
    "account": [
        ("A0", "login/", mobile_login_view.View, "移动端登录"),
        ("A1", "logout/", mobile_logout_view.View, "移动端退出登录"),
        ("A2", "profile/", mobile_profile_view.View, "查询个人信息"),
        ("A3", "profile/update/", mobile_profile_update_view.View, "修改个人信息"),
        ("A4", "profile/change_password/", mobile_change_password_view.View, "修改密码"),
    ],
    "menu": [
        ("B0", "list/", mobile_menu_view.View, "查询移动端菜单"),
    ],
}
