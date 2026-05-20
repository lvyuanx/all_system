from asgiref.sync import sync_to_async

from core.ninja_extra.api_extra import BaseApi, HttpRequest
from order.services import get_order_create_habit

from . import schemas


class View(BaseApi):

    api_status = BaseApi.ApiStatus.DEV_IN_PROGRESS
    methods = ["GET"]
    finally_code = "000", "查询订单创建习惯失败"
    response_schema = schemas.OrderCreateHabitSchema
    error_codes = []

    @staticmethod
    async def api(request: HttpRequest):
        return await sync_to_async(get_order_create_habit)(request.user.pk)
