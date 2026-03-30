# -*-coding:utf-8 -*-

"""
# File       : auth_channel_util.py
# Description: 认证通道配置工具
"""

from core.conf import settings


def _to_list(value, default=None) -> list[str]:
    if value is None:
        value = default or []

    if isinstance(value, str):
        value = [value]

    return [item for item in value if item]


def get_api_prefix() -> str:
    base = str(getattr(settings, "NINJA_BASE_URL", "api/")).strip("/")
    return f"/{base}/"


def get_mobile_api_prefix() -> str:
    return f"{get_api_prefix()}mobile/"


def normalize_path(path: str) -> str:
    path = str(path or "").strip()
    if not path:
        return ""
    return path.split("?", 1)[0]


def get_request_path(request) -> str:
    # 优先使用上游透传的原始 URI，避免代理重写导致的 path 丢失
    candidates = [
        request.META.get("HTTP_X_ORIGINAL_URI"),
        request.META.get("HTTP_X_REWRITE_URL"),
        request.META.get("RAW_URI"),
        request.META.get("REQUEST_URI"),
        request.get_full_path() if hasattr(request, "get_full_path") else None,
        getattr(request, "path", ""),
    ]
    for item in candidates:
        path = normalize_path(item)
        if path:
            return path
    return ""


def resolve_channel(path: str) -> str:
    path = str(path or "")
    mobile_prefix = get_mobile_api_prefix()
    # 兼容网关前缀场景：例如 /prod/api/mobile/...
    if path.startswith(mobile_prefix) or mobile_prefix in path or "/mobile/" in path:
        return "mobile"
    return "admin"


def resolve_channel_by_request(request) -> str:
    return resolve_channel(get_request_path(request))


def get_channel_config(channel: str) -> dict:
    channels = getattr(settings, "AUTH_CHANNELS", {}) or {}
    channel_conf = channels.get(channel, {}) if isinstance(channels, dict) else {}

    default_tag = getattr(settings, "TOKEN_TAG", "X-Authorization")
    default_read = ["cookie"] if channel == "admin" else []
    default_write = ["cookie"] if channel == "admin" else []
    default_return_token_in_body = channel != "admin"

    read_from = _to_list(channel_conf.get("read_from"), default_read)
    write_to = _to_list(channel_conf.get("write_to"), default_write)

    return {
        "channel": channel,
        "token_tag": channel_conf.get("token_tag", default_tag),
        "read_from": read_from,
        "write_to": write_to,
        "return_token_in_body": bool(
            channel_conf.get("return_token_in_body", default_return_token_in_body)
        ),
    }
