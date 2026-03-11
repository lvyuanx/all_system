

from django.shortcuts import render


def add_pattern(request):
    context = {
        "title": "添加版式",
    }
    return render(request, "pattern_library/pattern_edit.html", context)


def change_pattern(request, pid: int):
    context = {
        "title": "订单编辑",
        "pattern_id": pid,
    }
    return render(request, "pattern_library/pattern_edit.html", context)


def search_pattern(request):
    context = {
        "title": "图库搜索",
    }
    return render(request, "pattern_library/pattern_search.html", context)