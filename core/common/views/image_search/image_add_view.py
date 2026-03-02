# -*-coding:utf-8 -*-

"""
# File       : image_add_view.py
# Time       : 2026-02-28 17:16:39
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 上传图片到图库
"""

from ninja import Query
from core.ninja_extra.api_extra import BaseApi, HttpRequest, UploadedFile, File

from core.common.image_search_engine import get_image_search_manager


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["POST"]
    finally_code = "000", "上传图片到图库失败"
    response_schema = None
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest, image: UploadedFile = File(...), group: str = Query(default="default", description="图库分组名称")):
        image_search_manager = get_image_search_manager()
        
        engine = image_search_manager.get_engine(group)

        # Django 的 UploadedFile 对象用 .name
        file_name = image.name

        # 读取文件内容
        file_bytes = image.read()  # Django 的 UploadedFile.read() 是同步方法

        # 添加图片
        engine.add_images([(file_name, file_bytes)])