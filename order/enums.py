from django.db import models


class OrderTypeChoices(models.IntegerChoices):
    CLIENT = 1, "客户订单"
    PEER_TRANSFER = 2, "同行转单"


class OrderStatusChoices(models.IntegerChoices):
    CANCELED = 0, "取消"
    CREATED = 1, "创建"
    CONFIRMATION = 2, "订单确认"
    SUBMIT = 3, "订单提交"
    PRODUCTION = 4, "生产中"
    ENDED = 99, "结束"


class OrderPayStatusChoices(models.IntegerChoices):
    NOT_PAID = 1, "未支付"
    PAID_PARTIAL = 2, "部分支付"
    PAID = 99, "全部支付"


class OrderPayMehtodChoices(models.IntegerChoices):
    ALIPAY = 1, "支付宝"
    WECHAT = 2, "微信"
    CASH = 3, "现金"
    BANK = 4, "银行转账"
    

class OrderDeliveryChoices(models.IntegerChoices):
    DELIVERY = 1, "配送"
    SELF_DELIVERY = 2, "自提"
    EXPRESS = 3, "快递"
    OTHER = 4, "其他"


class OrderShipStatusChoices(models.IntegerChoices):
    NOT_SHIPPED = 1, "未发货"
    PARTIAL_SHIPMENT = 2, "部分发货"
    SHIPPED = 99, "已全部发货"