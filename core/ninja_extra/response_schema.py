# -*-coding:utf-8 -*-

"""
# File       : response_schema.py
# Time       : 2025-07-28 10:09:31
# Author     : lyx
# version    : python 3.11
# Description: 响应结构
"""
from typing import TypeVar, Optional, Generic
from pydantic import Field, BaseModel, model_validator

from core.ninja_extra.const import ResponseLevel

T = TypeVar("T")


class ResponseBaseSchema(BaseModel, Generic[T]):
    """通用响应结构"""

    code: Optional[str] = Field(default="0", description="状态码")
    msg: str = Field(default="success", description="状态信息")
    data: Optional[T] = Field(default=None, description="返回数据")
    level: Optional[ResponseLevel] = Field(default=ResponseLevel.SUCCESS, description="响应级别")

    model_config = {
        "validate_assignment": True,
        "arbitrary_types_allowed": True,
        "populate_by_name": True,
    }


class SuccessResponse(ResponseBaseSchema[T]):
    """成功响应，code 必须为 0"""

    @model_validator(mode="after")
    def validate_code_is_zero(cls, model):
        if model.code != "0":
            raise ValueError("SuccessResponse 的 code 必须为 0")
        return model


class ErrorResponse(ResponseBaseSchema[T]):
    """错误响应，code 必须为非 0 或可省略"""

    level: Optional[ResponseLevel] = Field(default=ResponseLevel.ERROR, description="响应级别")

    @model_validator(mode="after")
    def validate_code_not_zero(cls, model):
        if model.code is None or model.code == "0":
            raise ValueError("ErrorResponse 的 code 必须为非 0")
        return model


class BaseLevel:
    def __init__(self, msg: str):
        self.msg = msg
        
    def __str__(self):
        return self.msg
    
    @property
    def level(self):
        return ResponseLevel.SUCCESS



class Success(BaseLevel):
    pass

class Info(BaseLevel):
    
    @property
    def level(self):
        return ResponseLevel.INFO

class Warning(BaseLevel):
    
    @property
    def level(self):
        return ResponseLevel.WARNING

class Error(BaseLevel):

    @property
    def level(self):
        return ResponseLevel.ERROR