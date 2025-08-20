from django.urls import path
from core.conf import settings
from core.ninja_extra.response_schema import SuccessResponse, ErrorResponse

from core.ninja_extra.api_extra import NinjaAPIExtra
from core.status_codes import code_dict


api = NinjaAPIExtra(
    code_dict=code_dict, 
    title=settings.NINJA_TITLE, 
    version=settings.NINJA_VERSION, 
    description=settings.NINJA_DESCRIPTION,
    exception_handler=settings.NINJAT_EXCEPTION_HANDLERS | settings._NINJAT_EXCEPTION_HANDLERS
).api  # 增强的ninja_api

NINJA_BASE_URL = settings.NINJA_BASE_URL
urls = [
    path(NINJA_BASE_URL, api.urls),
]