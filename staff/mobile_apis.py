from .views import mobile_staff_info_view, mobile_staff_manage_views

apis = {
    "staff": [
        ("A0", "info/", mobile_staff_info_view.View, "移动端员工信息"),
        ("A1", "list/", mobile_staff_manage_views.StaffListView, "移动端员工分页列表"),
        ("A2", "detail/", mobile_staff_manage_views.StaffDetailView, "移动端员工详情"),
        ("A3", "activate/", mobile_staff_manage_views.StaffActivateView, "移动端启用员工账号"),
        ("A4", "deactivate/", mobile_staff_manage_views.StaffDeactivateView, "移动端禁用员工账号"),
        ("A5", "update_groups/", mobile_staff_manage_views.StaffUpdateGroupsView, "移动端修改员工权限组"),
        ("A6", "group_options/", mobile_staff_manage_views.StaffGroupOptionsView, "移动端权限组选项"),
    ],
}
