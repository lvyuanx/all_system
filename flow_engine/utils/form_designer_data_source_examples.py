# -*- coding:utf-8 -*-

from __future__ import annotations

from copy import deepcopy


BUILTIN_FORM_DATA_SOURCE_EXAMPLES = [
    {
        "code": "default.context.current_node_amount",
        "target": "default",
        "source_type": "context",
        "title": "从流程上下文回填节点金额",
        "description": "适合将上一节点或运行时上下文中的值带入当前字段默认值。",
        "config": {
            "source_type": "context",
            "context_path": "form.NODE_A.amount",
        },
    },
    {
        "code": "default.enum.order_status",
        "target": "default",
        "source_type": "enum",
        "title": "从订单状态枚举选择默认项",
        "description": "当枚举项中存在默认值时，字段会优先命中默认项。",
        "config": {
            "source_type": "enum",
            "enum_code": "order.status",
            "default_name": "PENDING",
        },
    },
    {
        "code": "default.db.order_receiver_name",
        "target": "default",
        "source_type": "db",
        "title": "从订单表读取收货人姓名",
        "description": "依赖内置数据库数据源 `order.field`，按字段名取单值。",
        "config": {
            "source_type": "db",
            "db_source_code": "order.field",
            "db_params": {
                "field": "receiver_name",
            },
        },
    },
    {
        "code": "options.enum.order_status",
        "target": "options",
        "source_type": "enum",
        "title": "使用订单状态枚举生成选项",
        "description": "适合单选、下拉等静态但可复用的选项来源。",
        "config": {
            "source_type": "enum",
            "enum_code": "order.status",
        },
    },
    {
        "code": "options.db.site_address_by_order",
        "target": "options",
        "source_type": "db",
        "title": "按订单所属站点加载地址选项",
        "description": "依赖内置数据库数据源 `site.address_options_by_order` 返回选项列表。",
        "config": {
            "source_type": "db",
            "db_source_code": "site.address_options_by_order",
        },
    },
]


def get_builtin_form_data_source_examples():
    return deepcopy(BUILTIN_FORM_DATA_SOURCE_EXAMPLES)
