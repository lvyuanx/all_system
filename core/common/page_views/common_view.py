# views.py
from django.http import HttpResponse

def dynamic_rendering_html_view(request, html_content):
    return HttpResponse(html_content)
