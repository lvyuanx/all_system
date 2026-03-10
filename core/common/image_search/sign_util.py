import hashlib
from typing import Dict, Optional

from core.utils import time_util



class SignUtil:
    def __init__(self, appid: str, secret_key: str, timeout: int = 300):
        """
        :param appid: 接口 appid
        :param secret_key: 接口 secret_key
        :param timeout: 默认超时时间（秒）
        """
        self.appid = appid
        self.secret_key = secret_key
        self.timeout = timeout

    @staticmethod
    def _filter_params(params: Dict) -> Dict[str, str]:
        """
        过滤 None 和 "" 参数
        """
        return {
            k: str(v)
            for k, v in params.items()
            if v is not None and str(v).strip() != ""
        }

    def create_sign(
        self,
        params: Dict[str, str],
        timestamp: Optional[int] = None,
        timeout: Optional[int] = None,
    ) -> Dict[str, str]:
        """
        生成签名，并返回带 timestamp 的参数字典

        :param params: 请求参数
        :param timestamp: 可指定时间戳
        :param timeout: 可指定超时时间（秒），否则使用默认 self.timeout
        :return: 新字典，带 timestamp 和 sign
        """

        if timestamp is None:
            timestamp = int(time_util.now_timestamp())

        # 使用传入 timeout，否则使用默认
        timeout = timeout if timeout is not None else self.timeout

        # 1️⃣ 过滤参数
        params_to_sign = self._filter_params(params)

        # 2️⃣ 添加系统参数
        params_to_sign["timestamp"] = str(timestamp)
        params_to_sign["appid"] = self.appid
        params_to_sign["timeout"] = str(timeout)

        # 3️⃣ 排序
        sorted_items = sorted(params_to_sign.items())
        param_str = "&".join(f"{k}={v}" for k, v in sorted_items)

        # 4️⃣ 拼接 secret_key
        raw_str = f"{param_str}&secret_key={self.secret_key}"

        # 5️⃣ 生成 sign
        sign = hashlib.md5(raw_str.encode("utf-8")).hexdigest().upper()

        # 6️⃣ 返回参数
        params_to_sign["sign"] = sign
        return params_to_sign
