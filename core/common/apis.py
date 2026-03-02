from django.conf import settings
from .views import get_province_view, get_city_view, get_district_view
from .views.image_search import image_add_view, image_delete_view, image_search_view, image_lib_init_view, image_list_view

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
    
    apis["image_search"] = [
        ("D0", "add", image_lib_init_view.View, "初始化图库"),
        ("D1", "add", image_add_view.View, "添加图片到图库"),
        ("D2", "del", image_delete_view.View, "从图库删除图片"),
        ("D3", "search", image_search_view.View, "以图搜图"),
        ("D4", "list", image_list_view.View, "查看图库中的图片列表"),
    ]
    