from django.urls import path
from .page_views.pattern_page import add_pattern

urls = [
    path("pattern_library/pattern/add/", add_pattern, name="add_pattern"),
]