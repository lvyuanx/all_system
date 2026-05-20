from asgiref.sync import async_to_sync
from django.test import RequestFactory, TestCase

from core.auth.models import User
from core.exceptions.base_exceptions import SysException
from core.ninja_extra.api_extra import BaseApi


class BaseApiPermissionWrapperTests(TestCase):
    def test_permission_check_runs_safely_in_async_api_wrapper(self):
        class ProtectedApi(BaseApi):
            perms_all = ["auth.view_permission"]

            @staticmethod
            async def api(request):
                return {"ok": True}

        user = User.objects.create_user(
            username="api-perm-user",
            phone="13900001000",
            password="123456",
        )
        request = RequestFactory().get("/api/protected/")
        request.user = user

        with self.assertRaises(SysException) as cm:
            async_to_sync(ProtectedApi.api)(request=request)

        self.assertEqual(cm.exception.code, "403")
