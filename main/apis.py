from core.ninja_extra.apis import apis as CORE_APIS
from core.auth.apis import apis as AUTH_APIS

apis = [
    ("A0", "core", CORE_APIS, "核心模块"),
    ("A1", "auth", AUTH_APIS, "用户模块"),
]