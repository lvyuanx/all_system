from django.urls import path
from .page_views.common_view import dynamic_rendering_html_view


urls = [
    path("common/rendering_html/", dynamic_rendering_html_view, name="dynamic_rendering_html_view"),
]
