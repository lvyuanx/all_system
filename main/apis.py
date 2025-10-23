from core.ninja_extra.apis import apis as CORE_APIS
from core.auth.apis import apis as AUTH_APIS
from staff.apis import apis as STAFF_APIS
from bill.apis import apis as BILL_APIS
from core.common.apis import apis as COMMON_APIS

apis = [
    ("A0", "core", CORE_APIS, "核心模块"),
    ("A1", "auth", AUTH_APIS, "用户模块"),
    ("A2", "staff", STAFF_APIS, "员工模块"),
    ("A3", "bill", BILL_APIS, "票据模块"),
    ("A4", "common", COMMON_APIS, "公共模块"),
]