from django.urls import path
from .page_views.pattern_page import add_pattern, change_pattern

urls = [
    path("pattern_library/pattern/add/", add_pattern, name="add_pattern"),
    path("pattern_library/pattern/<int:pid>/change/", change_pattern, name="change_pattern"),
]