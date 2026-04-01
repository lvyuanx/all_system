from core.ninja_extra.apis import apis as CORE_APIS
from core.auth.apis import apis as AUTH_APIS
from core.auth.mobile_apis import apis as AUTH_MOBILE_APIS
from staff.apis import apis as STAFF_APIS
from bill.apis import apis as BILL_APIS
from core.common.apis import apis as COMMON_APIS
from site_mgmt.apis import apis as SITE_MGMT_APIS
from client_mgmt.apis import apis as CLIENT_MGMT_APIS
from pattern_library.apis import apis as PATTERN_LIBRARY_APIS
from order.apis import apis as ORDER_APIS
from pattern_library.mobile_apis import apis as PATTERN_LIBRARY_MOBILE_APIS

apis = [
    ("A0", "core", CORE_APIS, "核心模块"),
    ("A1", "auth", AUTH_APIS, "用户模块"),
    ("A2", "staff", STAFF_APIS, "员工模块"),
    ("A3", "bill", BILL_APIS, "票据模块"),
    ("A4", "common", COMMON_APIS, "公共模块"),
    ("A5", "site_mgmt", SITE_MGMT_APIS, "站点管理模块"),
    ("A6", "client_mgmt", CLIENT_MGMT_APIS, "客户管理模块"),
    ("A7", "pattern_library", PATTERN_LIBRARY_APIS, "版式库模块"),
    ("A8", "order", ORDER_APIS, "订单模块"),
    ("M1", "mobile/auth", AUTH_MOBILE_APIS, "移动端用户模块"),
    ("M2", "mobile/pattern_library", PATTERN_LIBRARY_MOBILE_APIS, "移动端版式库模块"),
]
