

from django.shortcuts import render


def add_pattern(request):
    context = {
        "title": "添加版式",
    }
    return render(request, "pattern_library/pattern_add.html", context)