import socket
from unittest import mock

from asgiref.sync import async_to_sync
from django.test import RequestFactory, SimpleTestCase, TestCase

from core.auth.models import User
from core.exceptions.base_exceptions import SysException
from core.ninja_extra.api_extra import BaseApi
from core.ninja_extra.management.commands.uvserver import Command


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


class UvserverCommandTests(SimpleTestCase):
    def test_handle_falls_back_when_hostname_cannot_be_resolved(self):
        command = Command()

        async def noop_start():
            return None

        options = {
            "host": "0.0.0.0",
            "port": 8000,
            "workers": 1,
            "reload": False,
            "loop": "auto",
            "log_level": "info",
        }

        with mock.patch.object(command, "_start", noop_start), mock.patch(
            "socket.gethostbyname", side_effect=socket.gaierror(8, "not known")
        ):
            command.handle(**options)

        self.assertEqual(command.ip_address, "127.0.0.1")
