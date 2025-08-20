from core.status_codes import code_dict
from core.ninja_extra.response_schema import BaseLevel

_no_register_code = "3"   # 未注册接口code的状态码

class BaseException(Exception):
    def __init__(self, message: str, code=1):
        self.message = message
        self.code = code
        super().__init__(self.message)
        

class SysException(BaseException):
    def __init__(self, message: str | BaseLevel, code=1, data: dict = None):
        self.message = message
        if data:
            if isinstance(message, BaseLevel):
                self.message.msg =  self.message.msg.format(**data)
            else:
                self.message = self.message.format(**data)
        self.code = code
        self.data = data
        super().__init__(self.message, self.code)


class SysCodeException(BaseException):
    """系统码异常"""
    def __init__(self, code, data: dict = None, level=None):
        message = code_dict[code]
        if data:
            message = message.format(**data)
        super().__init__(message, code, level)


class NotRegisteredCodeException(SysCodeException):

    def __init__(self, code):
        super().__init__(_no_register_code, {"code": code})


class SysConfigException(BaseException):
    def __init__(self, name: str):
        message = f"系统配置 {name} 不存在"
        super().__init__(message, 2)


class BusinessException(BaseException):
    """业务异常"""

    def __init__(self, code=3, data:dict = None):
        self.code = code
        self.data = data

    @property
    def error_code(self) -> str:
        return self.code
        
