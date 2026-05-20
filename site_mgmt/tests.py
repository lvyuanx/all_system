from types import SimpleNamespace

from asgiref.sync import async_to_sync
from django.test import SimpleTestCase

from core.utils import common_util
from site_mgmt.utils import site_util
from site_mgmt.views.cur_site_options_view import View


class CurSiteOptionsViewTests(SimpleTestCase):
    def test_api_uses_async_site_utility_for_staff_site_options(self):
        async def fake_aget_cur_sites(request):
            return [
                SimpleNamespace(pk=1, site_name="站点A"),
                SimpleNamespace(pk=2, site_name="站点B"),
            ]

        async def fake_get_user_async(request):
            return request.user

        original_aget_cur_sites = site_util.aget_cur_sites
        original_get_user_async = common_util.get_user_async
        site_util.aget_cur_sites = fake_aget_cur_sites
        common_util.get_user_async = fake_get_user_async
        try:
            result = async_to_sync(View.api)(SimpleNamespace(user=SimpleNamespace(is_superuser=False)))
        finally:
            site_util.aget_cur_sites = original_aget_cur_sites
            common_util.get_user_async = original_get_user_async

        options = result.data
        self.assertEqual([item.value for item in options], [1, 2])
        self.assertEqual([item.label for item in options], ["站点A", "站点B"])
