import os
import re
from urllib.parse import urlparse

from core.exceptions.base_exceptions import BaseException
from core.utils.http_client import http_client
from .sign_util import SignUtil
from django.conf import settings

sign_util = SignUtil(settings.IMAGE_SEARCH_APPID, settings.IMAGE_SEARCH_SECRET_KEY)


def _http_response(res, url_path):
    if res.get("code") != 0:
        raise BaseException(code=str(res.get("code")), message=res.get("msg"))

    return res.get("data")


async def image_list(group, page=1, page_size=20, keyword="", order="desc"):
    url = settings.IMAGE_SEARCH_BASE_URL + "/image"
    url_path = urlparse(url).path
    params = {
        "group": group,
        "page": page,
        "page_size": page_size,
        "keyword": keyword,
        "order": order,
        "url": url_path,
    }
    sign_params = sign_util.create_sign(params)
    res = await http_client.get(
        url,
        params=sign_params,
    )

    return _http_response(res, url_path)


async def image_add(file, md5, group, filename, content_type):

    url = settings.IMAGE_SEARCH_BASE_URL + "/image"
    url_path = urlparse(url).path

    params = {"md5": md5, "group": group, "url": url_path}
    sign_params = sign_util.create_sign(params)

    files = {
        "file": (filename, file, content_type)
    }

    res = await http_client.post(
        url,
        params=sign_params,
        files=files,
    )

    _http_response(res, url_path)

async def rebuild():
    url = settings.IMAGE_SEARCH_BASE_URL + "/image/rebuild"
    url_path = urlparse(url).path
    params = {"url": url_path}
    sign_params = sign_util.create_sign(params)
    res = await http_client.get(url, params=sign_params)
    _http_response(res, url_path)


async def image_clear(group):
    url = settings.IMAGE_SEARCH_BASE_URL + "/image/clear"
    url_path = urlparse(url).path
    params = {"group": group, "url": url_path}
    sign_params = sign_util.create_sign(params)
    res = await http_client.delete(url, params=sign_params)
    _http_response(res, url_path)


async def image_delete(name):
    url = settings.IMAGE_SEARCH_BASE_URL + "/image"
    url_path = urlparse(url).path
    params = {"origin_name": name, "url": url_path}
    sign_params = sign_util.create_sign(params)
    res = await http_client.delete(url, params=sign_params)
    _http_response(res, url_path)


async def image_search(file, md5, group):
    url = settings.IMAGE_SEARCH_BASE_URL + "/image/search"
    url_path = urlparse(url).path
    params = {"md5": md5, "group": group, "url": url_path}
    sign_params = sign_util.create_sign(params)
    filename = os.path.basename(urlparse(file.name).path)
    res = await http_client.post(
        url,
        files={
            "file": (
                filename,
                file.file,
                file.content_type or "image/jpeg",
            )
        },
        params=sign_params,
    )
    return _http_response(res, url_path)

async def get_quota():
    url = settings.IMAGE_SEARCH_BASE_URL + "/auth/quota"
    url_path = urlparse(url).path
    params = {"url": url_path}
    sign_params = sign_util.create_sign(params)
    res = await http_client.post(
        url,
        params=sign_params,
    )
    return _http_response(res, url_path)


async def redeem_jdk(code: str):
    url = settings.IMAGE_SEARCH_BASE_URL + "/auth/jdk/redeem"
    url_path = urlparse(url).path
    params = {"url": url_path, "code": code}
    sign_params = sign_util.create_sign(params)
    res = await http_client.post(
        url,
        params=sign_params,
    )
    _http_response(res, url_path)