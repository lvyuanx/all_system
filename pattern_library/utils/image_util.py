# -*-coding:utf-8 -*-

"""
# File       : image_util.py
# Description: 图像无损压缩工具
"""

from io import BytesIO
from typing import Iterable, List

from PIL import Image
from django.core.files.uploadedfile import InMemoryUploadedFile, UploadedFile


def _safe_seek(file_obj, pos: int = 0):
    try:
        file_obj.seek(pos)
    except Exception:
        pass


def compress_uploaded_image_lossless(file: UploadedFile) -> UploadedFile:
    """
    对上传图片进行无损压缩（尽量不损失画质）。
    - PNG: optimize=True
    - WEBP: lossless=True
    - JPEG: 质量设为100并启用optimize（接近无损）
    非图片或处理失败则返回原文件。
    """
    if not file:
        return file

    _safe_seek(file, 0)
    try:
        img = Image.open(file)
        fmt = (img.format or "").upper()
    except Exception:
        _safe_seek(file, 0)
        return file

    output = BytesIO()
    try:
        if fmt in {"PNG"}:
            img.save(output, format=fmt, optimize=True)
        elif fmt in {"WEBP"}:
            img.save(output, format=fmt, lossless=True, quality=100, method=6)
        elif fmt in {"JPEG", "JPG"}:
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.save(
                output,
                format="JPEG",
                optimize=True,
                quality=100,
                subsampling=0,
            )
        else:
            # 其他格式直接返回原文件
            _safe_seek(file, 0)
            return file
    except Exception:
        _safe_seek(file, 0)
        return file

    output.seek(0)
    content_type = file.content_type or Image.MIME.get(fmt, None) or "application/octet-stream"
    return InMemoryUploadedFile(
        output,
        field_name=getattr(file, "field_name", "file"),
        name=file.name,
        content_type=content_type,
        size=output.getbuffer().nbytes,
        charset=None,
    )


def compress_uploaded_images_lossless(files: Iterable[UploadedFile]) -> List[UploadedFile]:
    if not files:
        return []
    return [compress_uploaded_image_lossless(f) for f in files]
