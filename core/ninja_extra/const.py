from enum import StrEnum


class ResponseLevel(StrEnum):
    """返回值级别"""

    # 接口成功
    SUCCESS = "s"
    
    # 接口失败
    ERROR = "e"
    WARNING = "w"
    INFO = "i"

    