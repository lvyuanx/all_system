from core.common.views.image_search import (
    image_search_view,
    image_search_quota_view,
    image_redeem_jdk_view,
)
from pattern_library.views import pattern_search_view
from order.views import mobile_order_list_by_pattern_view

apis = {
    "image_search": [
        ("A0", "search/", image_search_view.View, "移动端以图搜图"),
        ("A1", "quota/", image_search_quota_view.View, "移动端查询剩余搜索次数"),
        ("A2", "redeem_jdk/", image_redeem_jdk_view.View, "移动端JDK兑换"),
    ],
    "pattern": [
        ("B0", "search/", pattern_search_view.View, "移动端图片匹配版式"),
    ],
    "order": [
        ("C0", "list_by_pattern/", mobile_order_list_by_pattern_view.View, "移动端按版号查询订单"),
    ],
}
