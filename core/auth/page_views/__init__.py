from django.shortcuts import render

def my_view(request):
    context = {
        "title": "Hello Django",
        "message": "这是一个模板页面"
    }
    return render(request, "my_template.html", context)
