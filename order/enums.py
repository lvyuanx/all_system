from django.db import models


class OrderTypeChoices(models.IntegerChoices):
    CLIENT = 1, "客户订单"
    PEER_TRANSFER = 2, "同行转单"


from django.db import models


class OrderStatusChoices(models.IntegerChoices):
    CANCELED = 0, "已取消"

    CREATED = 10, "已创建"          # 录入订单
    CONFIRMED = 20, "已确认"        # 审核通过/客户确认

    SCHEDULED = 30, "已排产"        # 已进入排产计划
    PRODUCING = 40, "生产中"        # 正在生产
    FINISHED = 50, "已完工"         # 生产完成/待出库

    SHIPPED = 60, "已发货"          # 已出库/已发货
    COMPLETED = 70, "已完成"        # 签收/结案



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
    DELIVERY = 1, "送货上门"
    SELF_DELIVERY = 2, "自提"
    EXPRESS = 3, "快递"
    OTHER = 4, "其他"


class OrderShipStatusChoices(models.IntegerChoices):
    NOT_SHIPPED = 1, "未发货"
    PARTIAL_SHIPMENT = 2, "部分发货"
    SHIPPED = 99, "已全部发货"