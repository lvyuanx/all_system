# -*-coding:utf-8 -*-
"""订单数据看板 mock 数据"""

MOCK_SUMMARY = {
    "today_order_count": 18,
    "today_order_delta": 3,
    "today_amount": 36580,
    "today_amount_delta_rate": 8,
    "pending_ship": 25,
    "pending_pay": 12,
    "month_amount": 428900,
    "new_customer": 6,
}

MOCK_TREND = {
    "7": {
        "x": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        "count": [12, 18, 15, 22, 20, 25, 18],
        "amount": [2.1, 3.2, 2.8, 4.5, 3.9, 5.0, 3.6],
    },
    "30": {
        "x": [f"{i}日" for i in range(1, 31)],
        "count": [18, 14, 16, 19, 21, 23, 17, 18, 19, 20, 15, 17, 18, 19, 20, 22, 24, 18, 16, 21, 23, 19, 17, 18, 16, 20, 21, 19, 18, 17],
        "amount": [round(2 + i * 0.05, 1) for i in range(30)],
    },
    "90": {
        "x": [f"第{i}周" for i in range(1, 13)],
        "count": [72, 68, 75, 80, 85, 90, 78, 82, 88, 95, 86, 79],
        "amount": [round(8 + i * 0.3, 1) for i in range(12)],
    },
}

MOCK_STATUS = [
    {"value": 18, "name": "待确认"},
    {"value": 22, "name": "待排产"},
    {"value": 35, "name": "生产中"},
    {"value": 12, "name": "待发货"},
    {"value": 9, "name": "已发货"},
    {"value": 6, "name": "已完成"},
]

MOCK_SITE = [
    {"name": "广州站", "value": 58},
    {"name": "深圳站", "value": 46},
    {"name": "上海站", "value": 41},
    {"name": "成都站", "value": 35},
    {"name": "北京站", "value": 29},
]

MOCK_TYPE = [
    {"value": 40, "name": "定制"},
    {"value": 30, "name": "现货"},
    {"value": 20, "name": "补单"},
    {"value": 10, "name": "其他"},
]

MOCK_DELIVERY = [
    {"value": 45, "name": "快递"},
    {"value": 35, "name": "物流"},
    {"value": 20, "name": "自提"},
]

MOCK_PENDING_SHIP = [
    {"order_no": "SO20240318001", "site": "广州站", "customer": "华南客户A", "amount": "12,800", "time": "今天 10:24"},
    {"order_no": "SO20240318002", "site": "深圳站", "customer": "华南客户B", "amount": "8,450", "time": "今天 09:12"},
    {"order_no": "SO20240317015", "site": "上海站", "customer": "华东客户C", "amount": "5,900", "time": "昨天 16:40"},
    {"order_no": "SO20240317011", "site": "成都站", "customer": "西南客户D", "amount": "3,200", "time": "昨天 15:18"},
]

MOCK_PENDING_PAY = [
    {"order_no": "SO20240318005", "site": "广州站", "customer": "华南客户E", "amount": "21,300", "time": "今天 11:05"},
    {"order_no": "SO20240317021", "site": "北京站", "customer": "华北客户F", "amount": "9,880", "time": "昨天 18:10"},
    {"order_no": "SO20240317010", "site": "杭州站", "customer": "华东客户G", "amount": "7,150", "time": "昨天 14:05"},
    {"order_no": "SO20240316022", "site": "武汉站", "customer": "华中客户H", "amount": "4,760", "time": "前天 17:40"},
]
