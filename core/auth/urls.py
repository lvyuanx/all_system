from django.urls import path
from core.auth.page_views.role_page import role_create, role_change

app_name = "core.auth"

urls = [
    path("auth/group/add/", role_create, name="auth_group_add"),
    path("auth/group/<int:gid>/change/", role_change, name="auth_group_change"),
]