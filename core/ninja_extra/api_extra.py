# -*-coding:utf-8 -*-

"""
# File       : api_extra.py
# Time       : 2025-07-28 22:16:32
# Author     : lyx
# version    : python 3.11
# Description: ninja api 扩展
"""
from enum import StrEnum
from functools import wraps
import logging
from typing import Dict, List, Tuple, cast
from ninja import NinjaAPI, Router, Body, Query, Path, Schema, Header, UploadedFile, File, Form
from django.http.request import HttpRequest
from core.exceptions.base_exceptions import (
    SysException,
    BusinessException,
    NotRegisteredCodeException,
)
from core.conf import settings
from core.ninja_extra.response_schema import (
    ResponseBaseSchema,
    SuccessResponse,
    ErrorResponse,
    ResponseLevel,
    BaseLevel,
    Error,
    Info,
    Warning,
    Success,
)
from core.utils import data_util, common_util
from core.status_codes import code_dict
from ninja.utils import (
    contribute_operation_args,
    contribute_operation_callback,
    is_async_callable,
)
from core.ninja_extra.base_pagination import AsyncLimitOffsetPagination, paginate


logger = logging.getLogger(__name__)


class BaseApi:

    class ApiStatus(StrEnum):

        DEV_IN_PROGRESS = "🛠️"
        DEV_DONE = "✅"
        TEST_IN_PROGRESS = "🧪"
        TEST_DONE = "✔️"
        ARCHIVED = "📦"

    # 系统字段，请勿手动修改
    _router_code: str | int = None  # 路由代码
    _api_code: str | int = None  # 接口代码
    _merge_error_codes: Dict[str, str] = {}  # 合并的接口异常码,

    tags: list[str] = None  # 接口标签
    response_schema = None  # 成功响应结构
    error_response_schema = None  # 异常响应结构
    methods: list[str] = ["POST"]  # 接口方法类型
    api_status: str = ApiStatus.DEV_IN_PROGRESS  # 接口状态
    wrap_response: bool = True  # 是否包装响应

    # 分页
    is_pagination: bool = False
    pagination_class: AsyncLimitOffsetPagination = AsyncLimitOffsetPagination

    # 异常码
    finally_code: tuple | str = None
    error_codes: list[tuple | str] = []

    @staticmethod
    async def api(*args, **kwargs):
        raise NotImplementedError()

    @classmethod
    def _api_response_wrapper(cls):
        """处理api返回值"""

        def decorator(func):

            @wraps(func)
            async def wrapper(*args, **kwargs):
                response = await func(*args, **kwargs)
                if cls.wrap_response:
                    if isinstance(response, ResponseBaseSchema):
                        return response
                    return SuccessResponse(data=response)
                else:
                    return response

            return wrapper

        return decorator

    @classmethod
    def _api_exception_wrapper(cls):
        """处理api业务异常"""

        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):

                try:
                    return await func(*args, **kwargs)
                except BusinessException as e:
                    error_code = e.error_code
                    error_data = e.data
                    if error_code in code_dict:
                        message = code_dict[error_code]
                    else:
                        error_code = f"{cls._api_code}{error_code}"
                        if error_code not in cls._merge_error_codes.keys():
                            raise NotRegisteredCodeException(error_code)
                        message = cls._merge_error_codes[error_code]
                    raise SysException(
                        code=error_code, message=message, data=error_data
                    )

            return wrapper

        return decorator

    def __init_subclass__(cls) -> None:
        api_wrapper_func = cls.api
        if cls.is_pagination:
            pagination_class = cls.pagination_class
            assert pagination_class is not None, "分页器不能为空"
            api_wrapper_func = paginate(pagination_class)(api_wrapper_func)
            # contribute_operation_args(
            #     api_wrapper_func,
            #     "ninja_pagination",
            #     pagination_class.Input,
            #     pagination_class.InputSource,
            # )
        api_wrapper_func = cls._api_response_wrapper()(api_wrapper_func)
        api_wrapper_func = cls._api_exception_wrapper()(api_wrapper_func)
        setattr(cls, "api", api_wrapper_func)


class NinjaAPIExtra:

    def __init__(
        self,
        code_dict: dict,
        title: str,
        version: str,
        description: str,
        exception_handler: dict,
    ):
        self.ninja_api = NinjaAPI(
            openapi_url="openapi.json",  # 自定义 openapi.json 路径
            title=title,
            version=version,
            description=description,
        )
        self.exception_handler = exception_handler
        self.code_dict = code_dict
        self.register()
        self.add_exception_handlers()

    def add_exception_handlers(self):
        if not self.exception_handler:
            return
        for exce_str, handler_str in self.exception_handler.items():
            exc_class = common_util.import_func_or_class(exce_str)
            handler_func = common_util.import_func_or_class(handler_str)
            self.ninja_api.add_exception_handler(
                exc_class=exc_class, handler=handler_func
            )

    @property
    def api(self) -> NinjaAPI:
        return self.ninja_api

    def _url_join(self, *urls: str) -> str:
        """
        拼接多个 URL 片段，确保每个片段之间只有一个斜杠
        """
        if not urls:
            return ""
        cleaned = [u.strip("/") for u in urls if u]
        start = "/" if urls[0].startswith("/") else ""
        end = "/" if urls[-1].endswith("/") else ""
        return start + "/".join(cleaned) + end

    def get_code_and_msg(
        self, code: str | Tuple[str, str], api_code: str, code_dict: dict
    ):
        """
        获取状态码和消息
        """
        if not code:
            return None, None
        error_code = code
        error_msg = None
        if isinstance(error_code, str):
            if code in code_dict:
                error_msg = code_dict[error_code]
            else:
                raise SysException(f"[{error_code}]接口最终异常码不正确")
        elif isinstance(error_code, tuple) and len(error_code) == 2:
            error_code = f"{api_code}{code[0]}"
            error_msg = code[1]

        else:
            raise SysException(f"[{error_code}]接口最终异常码不正确")

        return error_code, error_msg

    def get_error_response(self, api_class: BaseApi):
        responses = {}
        for error_code, error_msg in api_class._merge_error_codes.items():
            if not isinstance(error_msg, BaseLevel):
                error_msg = Error(error_msg)
            responses[error_code] = {
                "description": error_msg.__str__(),
                "content": {
                    "application/json": {
                        "example": ErrorResponse(
                            code=error_code,
                            msg=error_msg.__str__(),
                            level=error_msg.level,
                            data=data_util.generate_example(
                                api_class.error_response_schema
                            ),
                        ).dict()
                    }
                },
            }

        return responses

    def set_api_attr(self, api_class: BaseApi, api_code: str, router_code: str):
        api_class._api_code = api_code
        api_class._router_code = router_code

        # 合并异常码，方便后续使用
        merge_codes: Dict[str, str] = {}
        code_dict = self.code_dict

        # 处理最终异常码
        finally_code, finally_msg = self.get_code_and_msg(
            api_class.finally_code, api_code, code_dict
        )
        if finally_code and finally_msg:
            merge_codes[finally_code] = finally_msg

        # 接口异常码
        for code in api_class.error_codes:
            error_code, error_msg = self.get_code_and_msg(code, api_code, code_dict)
            if error_code and error_msg:
                merge_codes[error_code] = error_msg

        api_class._merge_error_codes = merge_codes

    def register(self):
        ROOT_APICONF = settings.ROOT_APICONF
        apis_model = __import__(ROOT_APICONF, fromlist=["apis"])
        apis = getattr(apis_model, "apis", [])

        for router in apis:  # 遍历路由
            assert (
                isinstance(router, tuple) and len(router) == 4
            ), f"接口组配置格式错误: {router}"
            router_code, router_url, router_apis, router_desc = router

            router_obj = Router(tags=[router_desc])
            for api_group_prefix, api_group in router_apis.items():
                for api in api_group:  # 遍历API
                    assert isinstance(api, tuple) and (
                        4 <= len(api) <= 5
                    ), f"接口配置格式错误: {api}"

                    if len(api) == 4:  # 没有接口配置
                        api_code, api_url, api_class, api_desc = cast(
                            tuple[str, str, BaseApi, str], api
                        )
                        api_conf = {}
                    else:  # 携带接口配置
                        api_code, api_url, api_class, api_desc, api_conf = cast(
                            tuple[str, str, BaseApi, str, dict], api
                        )

                    interface_code = f"{router_code}{api_code}"  # 接口码
                    interface_url = self._url_join(api_group_prefix, api_url)

                    # 给接口赋值
                    self.set_api_attr(
                        api_class=api_class,
                        api_code=interface_code,
                        router_code=router_code,
                    )

                    view_func = api_class.api
                    if api_class.is_pagination:
                        pagination_class = api_class.pagination_class
                        contribute_operation_args(
                            view_func,
                            "ninja_pagination",
                            pagination_class.Input,
                            pagination_class.InputSource(...),
                        )
                        response = (
                            SuccessResponse[
                                pagination_class.Output[api_class.response_schema]
                            ]
                            | ErrorResponse[api_class.error_response_schema]
                        )
                    else:
                        response = (
                            SuccessResponse[api_class.response_schema]
                            | ErrorResponse[api_class.error_response_schema]
                        )

                    # 注册api到路由中
                    router_obj.add_api_operation(
                        path=interface_url,
                        methods=api_class.methods,
                        view_func=view_func,
                        summary=f"{api_class.api_status} {api_desc} {interface_code}",
                        tags=api_conf.get("tags"),
                        response=response,
                        openapi_extra={"responses": self.get_error_response(api_class)},
                    )

            # 添加路由
            self.ninja_api.add_router(
                prefix=router_url,
                router=router_obj,
                tags=[router_desc],
            )
