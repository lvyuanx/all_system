import json
from django.shortcuts import render


def home_page(request):
    user = request.user
    if user.is_superuser:
        context = {"title": "数据看板"}
        template = "custom_home/superuser_index.html"
    else:
        role_names = list(user.groups.values_list("name", flat=True))
        user_info = {
            "username": user.username,
            "name": user.get_full_name() or user.username,
            "email": user.email,
            "last_login": user.last_login and user.last_login.strftime("%Y-%m-%d %H:%M:%S"),
            "is_staff": user.is_staff,
            "roles": role_names,
        }

        context = {
            "title": "欢迎",
            "user_info_json": json.dumps(user_info, ensure_ascii=False),
        }
        template = "custom_home/user_index.html"
    return render(request, template, context)

