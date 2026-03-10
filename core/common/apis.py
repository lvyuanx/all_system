from django.conf import settings
from .views import get_province_view, get_city_view, get_district_view

apis = {
    "province": [
       ("A0", "page", get_province_view.View, "分页查询省份信息"),  
    ],
    "city": [
       ("B0", "page", get_city_view.View, "分页查询市信息"),  
    ],
    "district": [
       ("C0", "page", get_district_view.View, "分页查询区县信息"),  
    ],
}

if settings.DEBUG:
    from .views.image_search import image_list_view, image_add_view, image_rebuild_view, image_clear_view, image_delete_view, image_search_view
    apis["image_search"] = [
        ("D0", "list", image_list_view.View, "分页查询图片信息"),
        ("D1", "add", image_add_view.View, "添加图片信息"),
        ("D2", "rebuild", image_rebuild_view.View, "重建图片索引"),
        ("D3", "clear", image_clear_view.View, "清空图片索引"),
        ("D4", "delete", image_delete_view.View, "删除图片信息"),
        ("D5", "search", image_search_view.View, "以图搜图"),
    ]