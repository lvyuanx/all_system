# -*- coding:utf-8 -*-

from __future__ import annotations

from copy import deepcopy


BUILTIN_FORM_DATA_SOURCE_EXAMPLES = [
    {
        "code": "default.enum.order_status",
        "target": "default",
        "source_key": "order_status",
        "title": "默认值取订单状态枚举",
        "description": "通过内置订单状态数据源解析当前字段的默认值。",
        "config": {
            "mode": "data_source",
            "source_key": "order_status",
            "source_params": {
                "default_name": "PENDING",
            },
        },
    },
    {
        "code": "options.enum.order_status",
        "target": "options",
        "source_key": "order_status",
        "title": "选项取订单状态枚举",
        "description": "通过内置订单状态数据源生成可复用选项列表。",
        "config": {
            "mode": "data_source",
            "source_key": "order_status",
            "source_params": {},
        },
    },
    {
        "code": "options.db.site_address_by_order",
        "target": "options",
        "source_key": "site_address_select",
        "title": "选项取订单关联站点地址",
        "description": "根据当前订单加载关联站点地址选项。",
        "config": {
            "mode": "data_source",
            "source_key": "site_address_select",
            "source_params": {},
        },
    },
]


def get_builtin_form_data_source_examples():
    return deepcopy(BUILTIN_FORM_DATA_SOURCE_EXAMPLES)
