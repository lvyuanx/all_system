# http_client.py

import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class HttpClient:
    """
    通用异步 HTTP 客户端
    """

    def __init__(
        self,
        base_url: str = "",
        timeout: int = 10,
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
        await self.client.aclose()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=5),
    )
    async def request(
        self,
        method: str,
        url: str,
        params: Dict[str, Any] = None,
        json: Dict[str, Any] = None,
        data: Dict[str, Any] = None,
        headers: Dict[str, str] = None,
        files: Dict[str, Any] = None,
    ) -> Any:

        try:

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

            content_type = resp.headers.get("content-type", "")

            if "application/json" in content_type:
                return resp.json()

            return resp.text

        except httpx.HTTPStatusError as e:

            logger.error(
                "HTTP error %s %s status=%s body=%s",
                method,
                url,
                e.response.status_code,
                e.response.text,
            )

            raise

        except Exception as e:

            logger.exception("HTTP request failed %s %s", method, url)

            raise

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs):
        return await self.request("PUT", url, **kwargs)

    async def delete(self, url: str, **kwargs):
        return await self.request("DELETE", url, **kwargs)
