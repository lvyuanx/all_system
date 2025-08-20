from django.conf import settings

apis = {}


if settings.DEBUG:
    from .views import test_view
    apis["test"] = [
        ("A0", "test", test_view.View, "测试接口"),
    ]
    
    