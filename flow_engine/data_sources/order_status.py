# -*- coding:utf-8 -*-

from __future__ import annotations

from flow_engine.data_sources.base import BaseFieldDataSource, _MISSING
from flow_engine.utils.form_runtime_util import resolve_enum_options


class OrderStatusChoicesDataSource(BaseFieldDataSource):
    key = "order_status"
    label = "订单状态"
    data_type = "select"
    support_components = ["input", "number", "select", "radio", "checkbox"]

    def _get_default_value(self):
        options = resolve_enum_options(
            {
                "enum_code": "order.status",
                "default_name": self.source_params.get("default_name"),
                "default_value": self.source_params.get("default_value"),
            }
        )
        for item in options:
            if item.get("default"):
                return item.get("value")
        return _MISSING

    def get_default_text(self):
        return self._get_default_value()

    def get_default_number(self):
        return self._get_default_value()

    def get_default_options(self):
        return self._get_default_value()

    def get_options_options(self):
        return resolve_enum_options({"enum_code": "order.status"})
