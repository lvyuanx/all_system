from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory, TestCase, override_settings
from unittest.mock import AsyncMock, patch

import httpx

from core.common.views.image_search.image_search_quota_view import View as ImageSearchQuotaView
from core.auth.models import User
from core.middlewares.jwt_middleware import JWTMiddleware


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


class JWTMiddlewareTests(TestCase):
    @override_settings(SSO_MAX_MOBILE_SESSIONS=0)
    def test_token_uid_sets_request_user_for_mobile_api(self):
        user = User.objects.create_user(
            username="jwt-user",
            phone="13900000001",
            password="123456",
        )
        captured = {}

        def get_response(request):
            captured["user"] = request.user
            return object()

        request = RequestFactory().get(
            "/api/mobile/order/order/list/",
            HTTP_AUTHORIZATION="Bearer test-token",
        )
        request.user = AnonymousUser()

        with patch("core.middlewares.jwt_middleware.token_util.verify_token") as verify_token:
            verify_token.return_value = {"uid": user.pk, "client": "mobile"}
            JWTMiddleware(get_response)(request)

        self.assertEqual(captured["user"].pk, user.pk)
