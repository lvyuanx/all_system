# http_client.py

import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from core.utils import time_util

logger = logging.getLogger(__name__)


def _retry_for_server_error(exc: BaseException) -> bool:
    if isinstance(exc, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = getattr(exc.response, "status_code", 0)
        return int(status_code) >= 500
    return False


class HttpClient:
    """
    通用异步 HTTP 客户端
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout),
            headers=headers,
        )

    async def close(self):
        """
        关闭连接池
        """
        await self.client.aclose()

    @retry(
        retry=retry_if_exception(_retry_for_server_error),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=True,
    )
    async def request(
        self,
        method: str,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> Any:

        start = time_util.now_timestamp()

        try:

            logger.debug(
                f"HTTP Request {method} {url} "
                f"params={params} json={json}"
            )

            resp = await self.client.request(
                method=method,
                url=url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                files=files,
            )

            resp.raise_for_status()

            cost = (time_util.now_timestamp() - start) * 1000

            logger.info(
                f"⚡️ HTTP {method} {url} "
                f"status={resp.status_code} "
                f"{cost:.2f}ms"
            )

            content_type = resp.headers.get("content-type", "")

            if "application/json" in content_type:
                return resp.json()

            return resp.text

        except httpx.HTTPStatusError as e:

            logger.error(
                f"HTTP error {method} {url} "
                f"status={e.response.status_code} "
                f"body={e.response.text}"
            )

            raise

        except Exception:

            logger.exception(
                f"HTTP request failed {method} {url}"
            )

            raise

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self.request("DELETE", url, **kwargs)


http_client = HttpClient()
