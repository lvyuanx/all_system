# -*-coding:utf-8 -*-

"""
# File       : mobile_staff_info_view.py
# Description: mobile staff info (staff_code, site_name)
"""

from asgiref.sync import sync_to_async

from core.conf import settings
from core.ninja_extra.api_extra import BaseApi, BusinessException, Warning, HttpRequest
from core.utils import token_util, auth_channel_util
from core.auth.models import User
from staff.models import Staff

from .schemas import MobileStaffInfoSchema


SECRET_KEY = settings.SECRET_KEY


class View(BaseApi):
    api_status = BaseApi.ApiStatus.DEV_DONE
    methods = ["GET"]
    wrap_response = True
    response_schema = MobileStaffInfoSchema
    error_codes = [
        ("001", Warning("未登录或 Token 无效")),
        ("002", Warning("用户不存在")),
        ("003", Warning("员工信息不存在")),
    ]

    @staticmethod
    async def api(request: HttpRequest):
        channel_conf = auth_channel_util.get_channel_config("mobile")
        token = token_util.get_token_by_origins(
            request, channel_conf["token_tag"], channel_conf["read_from"]
        )
        if not token:
            raise BusinessException("001")

        try:
            payload = token_util.verify_token(token, SECRET_KEY)
        except Exception:
            raise BusinessException("001")

        uid = payload.get("uid")
        user: User = await sync_to_async(User.objects.filter(pk=uid).first)()
        if user is None:
            raise BusinessException("002")

        staff = await sync_to_async(
            Staff.objects.select_related("site").filter(user_id=uid).first
        )()
        if staff is None:
            raise BusinessException("003")

        return MobileStaffInfoSchema(
            staff_code=staff.staff_code,
            site_name=staff.site.site_name if staff.site else None,
        )
