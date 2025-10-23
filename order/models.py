from decimal import Decimal
from django.db import models
from django.db.models import F

from core.conf import settings
from core.utils import model_util
from core.common.generator import sn_generator
from order.enums import (
    OrderTypeChoices,
    OrderStatusChoices,
    OrderPayStatusChoices,
    OrderPayMehtodChoices,
    OrderDeliveryChoices,
    OrderShipStatusChoices,
)


class Order(
    model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model
):
    """订单表"""

    order_no = models.CharField(max_length=255, verbose_name="订单编号")
    order_type = models.IntegerField(
        choices=OrderTypeChoices.choices,
        default=OrderTypeChoices.CLIENT,
        verbose_name="订单类型",
    )
    order_status = models.IntegerField(
        choices=OrderStatusChoices.choices,
        default=OrderStatusChoices.CREATED,
        verbose_name="订单状态",
    )

    # 金额相关
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单原始总金额",
    )
    discount_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单优惠金额",
    )
    shipping_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单运费",
    )
    payable_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单应付金额",
    )
    paid_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单实付金额",
    )

    # 支付信息
    pay_status = models.IntegerField(
        choices=OrderPayStatusChoices.choices,
        default=OrderPayStatusChoices.NOT_PAID,
        verbose_name="订单支付状态",
    )
    pay_method = models.ImageField(
        choices=OrderPayMehtodChoices.choices,
        default=OrderPayMehtodChoices.ALIPAY,
        verbose_name="订单支付方式",
    )
    pay_time = models.BigIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name="订单支付时间",
    )

    # 发货信息
    shipping_party = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="订单发货方",
    )
    shipping_party_company = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="订单发货方公司名称",
    )
    shipping_party_phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="订单发货方电话",
    )
    shipping_party_address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="订单发货方地址",
    )
    delivery_method = models.IntegerField(
        choices=OrderDeliveryChoices.choices,
        default=OrderDeliveryChoices.DELIVERY,
        verbose_name="订单配送方式",
    )
    delivery_time = models.BigIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name="订单配送时间",
    )
    tracking_no = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="订单配送单号",
    )
    ship_status = models.IntegerField(
        choices=OrderShipStatusChoices.choices,
        default=OrderShipStatusChoices.NOT_SHIPPED,
        verbose_name="订单发货状态",
    )

    # 收货信息
    receiver_name = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="收货人姓名",
    )
    receiver_company = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="收货方公司名称",
    )
    receiver_phone = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="收货人电话",
    )
    receiver_address = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        default=None,
        verbose_name="收货人地址",
    )

    memo = models.TextField(null=True, blank=True, verbose_name="订单备注")

    @staticmethod
    def get_sn(count=1):
        return sn_generator.next_ids(
            count, prefix="T", used_for="order.Order", letter_length=0
        )

    def save(self, *args, **kwargs):
        if not self.salary_serial_number:  # 只有保存时才生成
            self.salary_serial_number = self.get_sn()[0]
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "订单管理"
        verbose_name_plural = verbose_name


class OrderItem(
    model_util.PermissionHelperMixin, model_util.StructureMoelMixin, models.Model
):
    """订单项表"""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        db_constraint=False,
        related_name="items",
        verbose_name="订单",
    )

    item_name = models.CharField(max_length=255, verbose_name="订单项名称")
    item_no = models.CharField(max_length=255, verbose_name="订单项编号")
    pattern_code = models.CharField(max_length=255, verbose_name="订单项款号")
    pattern_png = models.ImageField(
        upload_to=model_util.client_logo_path,
        blank=True,
        null=True,
        default=settings.DEFAULT_IMAGE,
        verbose_name="款号主图",
    )
    color = models.CharField(max_length=255, verbose_name="颜色")
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单项价格",
    )
    count = models.IntegerField(default=1, verbose_name="订单项数量")
    total = models.GeneratedField(
        expression=F("unit_price") * F("count"),
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
        db_persist=False,
        verbose_name="订单项总金额",
    )
    total_unit = models.CharField(max_length=255, verbose_name="订单项单位")
    discount_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="订单项优惠金额",
    )
    subtotal = models.GeneratedField(
        expression=F("total") - F("discount_price"),
        output_field=models.DecimalField(max_digits=10, decimal_places=2),
        db_persist=False,
        verbose_name="小计金额",
    )
    memo = models.TextField(null=True, blank=True, verbose_name="订单项备注")

    @staticmethod
    def get_sn(count=1):
        return sn_generator.next_ids(
            count, prefix="T", used_for="order.Order", letter_length=0
        )

    def save(self, *args, **kwargs):
        if self.item_no is None:
            self.item_no = self.get_sn()[0]
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = "订单项"
        verbose_name_plural = verbose_name
