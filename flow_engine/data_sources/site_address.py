# -*- coding:utf-8 -*-

from __future__ import annotations

from flow_engine.data_sources.base import BaseFieldDataSource
from flow_engine.utils.form_runtime_util import _resolve_db_options


class SiteAddressSelectDataSource(BaseFieldDataSource):
    key = "site_address_select"
    label = "站点地址选项"
    data_type = "select"
    support_components = ["select", "radio", "checkbox"]

    def get_options_options(self):
        legacy_config = {
            "db_source_code": "site.address_options_by_order",
            "db_params": self.source_params,
        }
        return _resolve_db_options(legacy_config, self.ctx, self.runtime_env)
