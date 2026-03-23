# -*-coding:utf-8 -*-
"""
二维码工具
"""
from __future__ import annotations

import base64
import io
from typing import Literal

try:
    import qrcode
    from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H
except ImportError as exc:  # pragma: no cover
    raise ImportError("缺少依赖 qrcode，请先安装：pip install qrcode[pil]") from exc

ErrorLevel = Literal["L", "M", "Q", "H"]

_ERROR_MAP = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


def generate_qr_png_bytes(
    data: str,
    *,
    box_size: int = 10,
    border: int = 4,
    error_level: ErrorLevel = "M",
    fill_color: str = "black",
    back_color: str = "white",
) -> bytes:
    """生成二维码 PNG 的二进制内容。"""
    if not isinstance(data, str):
        data = str(data)

    qr = qrcode.QRCode(
        version=None,
        error_correction=_ERROR_MAP.get(error_level, ERROR_CORRECT_M),
        box_size=box_size,
        border=border,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color=fill_color, back_color=back_color)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_qr_png_base64(
    data: str,
    *,
    box_size: int = 10,
    border: int = 4,
    error_level: ErrorLevel = "M",
    fill_color: str = "black",
    back_color: str = "white",
) -> str:
    """生成二维码 PNG 的 data URL（base64）。

    Args:
        data: 待编码文本/URL。
        box_size: 单个模块的像素大小。
        border: 边距（模块数）。
        error_level: 容错等级 L/M/Q/H。
        fill_color: 前景色。
        back_color: 背景色。
    Returns:
        data:image/png;base64,... 格式的字符串，可直接用于 img src。
    """
    png_bytes = generate_qr_png_bytes(
        data,
        box_size=box_size,
        border=border,
        error_level=error_level,
        fill_color=fill_color,
        back_color=back_color,
    )
    b64 = base64.b64encode(png_bytes).decode()
    return f"data:image/png;base64,{b64}"


__all__ = ["generate_qr_png_base64", "generate_qr_png_bytes"]
