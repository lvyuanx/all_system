# -*-coding:utf-8 -*-

"""
# File       : refresh_bill_pdf_view.py
# Time       : 2025-10-15 15:28:46
# Author     : lvyuanxiang
# version    : python 3.11
# Description: 更新票据PDF文件
"""
import logging
from asgiref.sync import sync_to_async
from bill.utils import pdf_util
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query, BusinessException
from ..models import Bill

logger = logging.getLogger("project")

class View(BaseApi):
    
    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "更新票据PDF文件失败"
    response_schema = None
    error_codes = [
        ("001", "票据不存在"),
        ("002", "PDF生成失败"),
    ]

    @staticmethod
    async def api(request: HttpRequest, pk: int = Query(..., description="票据ID")):
        
        bill_queryset = Bill.objects.filter(id=pk).values("template__content", "params")
        if not await bill_queryset.aexists():
            raise BusinessException("001")
        
        bill_dict = await bill_queryset.afirst()
                
        template_content = bill_dict.get("template__content")
        params = bill_dict.get("params")

        try:
            media_path = await sync_to_async(pdf_util.jinja2_to_pdf)(template_content, params)
        except Exception as e:
            logger.error(f"票据[{pk}]生成PDF失败，错误信息[{e}]", exc_info=True)
            raise BusinessException("002")
        logger.debug(f"票据[{pk}]生成PDF成功，保存路径[{media_path}]")
        await Bill.objects.filter(id=pk).aupdate(bill_path=media_path)