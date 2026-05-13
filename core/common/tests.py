from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase
from unittest.mock import AsyncMock, patch

import httpx

from core.common.views.image_search.image_search_quota_view import View as ImageSearchQuotaView


class ImageSearchQuotaViewTests(TestCase):
    def test_quota_fallback_to_zero_when_upstream_error(self):
        request = RequestFactory().get("/api/common/image_search/quota")
        request.user = AnonymousUser()
        with patch(
            "core.common.views.image_search.image_search_quota_view.image_search_adapter.get_quota",
            new=AsyncMock(side_effect=httpx.ConnectError("connect failed")),
        ):
            response = async_to_sync(ImageSearchQuotaView.api)(request=request)
        self.assertEqual(response.data, 0)

    def test_quota_returns_upstream_value(self):
        request = RequestFactory().get("/api/common/image_search/quota")
        request.user = AnonymousUser()
        with patch(
            "core.common.views.image_search.image_search_quota_view.image_search_adapter.get_quota",
            new=AsyncMock(return_value={"search_quota": 7}),
        ):
            response = async_to_sync(ImageSearchQuotaView.api)(request=request)
        self.assertEqual(response.data, 7)
