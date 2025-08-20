from django.shortcuts import render
from django.contrib.auth.models import Group

def role_create(request):
    context = {
        "title": "添加角色",
    }
    return render(request, "core_auth/role/role_create.html", context)


def role_change(request, gid: int):
    group = Group.objects.get(id=gid)
    context = {
        "title": "编辑角色",
        "gid": gid,
        "gname": group.name,
    }
    return render(request, "core_auth/role/role_update.html", context)
