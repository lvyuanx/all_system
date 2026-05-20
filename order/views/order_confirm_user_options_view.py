from asgiref.sync import sync_to_async

from core.exceptions.base_exceptions import BusinessException
from core.ninja_extra.api_extra import BaseApi, HttpRequest, Query
from order.services import get_confirm_user_options
from site_mgmt.utils import site_util

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询订单确认人失败"
    response_schema = list[schemas.OrderConfirmUserOptionSchema]
    error_codes = [
        ("001", "您没有该站点权限"),
    ]

    @staticmethod
    async def api(request: HttpRequest, site_id: int = Query(..., description="站点ID")):
        cur_sites = await site_util.aget_cur_sites(request)
        if site_id not in [item.pk for item in cur_sites]:
            raise BusinessException("001")
        return await sync_to_async(get_confirm_user_options)(site_id)
