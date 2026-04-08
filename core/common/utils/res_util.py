import os
import hashlib

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.http import HttpRequest
from django.db.models.query import QuerySet
from typing import Iterable, List, Union
from core.common.signals.signals import res_unactive_signal



def upload_res(
    request_or_uid: Union[HttpRequest, str, int],
    files,
    category=None,
    content_type=None,
    obj=None,
) -> Union[int, List[int]]:
    """
    支持单文件或多文件上传，带事务。
    - files: 单个文件对象或文件 Iterable
    - 返回单文件 id 或多文件 id 列表
    """
    from ..models import Resource

    # 转换成列表，统一处理
    single_file = False
    if  not isinstance(files, list):
        single_file = True
        files = [files]

    if not files:
        raise ValueError("files 参数不能为空")

    if not content_type and not obj:
        raise ValueError("content_type 和 obj 参数不能同时为空")

    # 自动识别 content_type
    if obj and not content_type:
        content_type = ContentType.objects.get_for_model(obj)

    # 获取上传者 uid
    if isinstance(request_or_uid, HttpRequest):
        uploader_id = request_or_uid.user.pk
    else:
        uploader_id = request_or_uid

    created_ids = []

    with transaction.atomic():  # 🔥 保证多个文件上传的原子性
        for f in files:
            if not f:
                raise ValueError("files 中发现空文件项")

            res = Resource(
                file=f,
                category=category,
                uploader_id=uploader_id,
                content_type=content_type,
            )
            res.save()
            created_ids.append(res.pk)

    # 如果只传 1 个文件，返回 int
    if single_file:
        return created_ids[0]

    return created_ids


def calc_file_md5(f, chunk_size=8192):
    """
    通用 MD5 文件摘要计算方法。
    支持:
    - Django UploadedFile
    - 文件路径字符串
    - 普通二进制文件对象 (readable)

    返回:
        32位 md5 字符串
    """
    md5 = hashlib.md5()

    # 如果是文件路径
    if isinstance(f, str):
        with open(f, "rb") as fp:
            for chunk in iter(lambda: fp.read(chunk_size), b""):
                md5.update(chunk)
        return md5.hexdigest()

    # 如果是 Django 的 UploadedFile 或其他 file-like object
    pos = None
    try:
        # 记录当前指针，用完后恢复，避免影响后续读取
        pos = f.tell()
    except Exception:
        pass  # 有些流不支持 tell()

    for chunk in iter(lambda: f.read(chunk_size), b""):
        md5.update(chunk)

    # 如果支持 seek，则恢复到原位置
    try:
        f.seek(pos)
    except Exception:
        pass

    return md5.hexdigest()


def unactive_res(res):
    from ..models import Resource
    if isinstance(res, int):
        res = Resource.objects.get(pk=res)
    with transaction.atomic():
        res.unactive()
        res_unactive_signal.send(
            sender=Resource,
            stored_name=res.stored_name,
        )


def batch_unactive_res(res: Union[List[int], QuerySet]):
    """
    批量禁用资源，保留 Resource.unactive() 的所有逻辑。
    支持传入 Resource id 列表或 Resource QuerySet。
    """
    from ..models import Resource
    # 将 list 转成 QuerySet，避免重复查询
    if isinstance(res, list):
        res_queryset = Resource.objects.filter(pk__in=res)
    else:
        res_queryset = res

    with transaction.atomic():
        # 避免每次循环都触发额外查询
        res_list = list(res_queryset)
        for r in res_list:
            r.unactive()
            res_unactive_signal.send(sender=Resource, stored_name=r.stored_name)


