# -*-coding:utf-8 -*-

"""
# File       : image_search_quota_view.py
# Time       : 2026-03-17 22:28:29
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 查询剩余搜索次数
"""

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from core.common.image_search import  image_search_adapter
import logging

logger = logging.getLogger(__name__)


class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询剩余搜索次数失败"
    response_schema = int
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        try:
            res = await image_search_adapter.get_quota()
        except Exception as exc:
            logger.warning(
                "fetch image search quota failed, fallback to 0: %s",
                exc,
            )
            return 0
        return (res or {}).get("search_quota", 0)
