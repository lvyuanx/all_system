from django.shortcuts import render


def home_page(request):
    context = {
        "title": "订单创建",
    }
    return render(request, "custom_home/index.html", context)