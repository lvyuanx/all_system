from django.conf import settings
from .views import get_province_view, get_city_view, get_district_view

apis = {
    "province": [
       ("A0", "page", get_province_view.View, "分页查询省份信息"),  
    ],
    "city": [
       ("A1", "page", get_city_view.View, "分页查询市信息"),  
    ],
    "district": [
       ("A2", "page", get_district_view.View, "分页查询区县信息"),  
    ]
}
    