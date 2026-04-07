from decimal import Decimal
from pydantic import BaseModel, Field


class OrderItemCreateSchema(BaseModel):
    """订单项创建参数"""

    pattern_code: str = Field(..., description="款号")
    color: str = Field(..., description="颜色")
    count: int = Field(..., description="数量")
    unit_price: Decimal = Field(..., description="单价")
    discount_price: Decimal = Field(..., description="优惠金额")
    total_unit: str = Field(..., description="单位")
    memo: str = Field(..., description="备注")


class OrderCreateSchema(BaseModel):
    """订单创建参数"""

    site_id: int = Field(..., description="站点ID")
    order_type: int = Field(..., description="订单类型")
    shipping_party: str = Field(..., description="发货方")
    shipping_party_phone: str = Field(..., description="发货方电话")
    shipping_party_address: str = Field(..., description="发货方地址")
    shipping_party_company: str = Field(..., description="发货方公司")
    delivery_method: int = Field(..., description="配送方式")
    receiver_name: str = Field(..., description="收货人姓名")
    receiver_phone: str = Field(..., description="收货人电话")
    receiver_address: str = Field(..., description="收货人地址")
    receiver_company: str = Field(..., description="收货方公司")
    memo: str = Field(..., description="备注")
    items: list[OrderItemCreateSchema] = Field(..., description="订单项")


class OrderInfoSchema(OrderCreateSchema):
    """订单信息"""

    order_id: int = Field(..., description="订单ID")


class OrderShipSchema(BaseModel):
    """订单发货"""

    order_id: int = Field(..., description="订单ID")
    delivery_method: int = Field(..., description="配送方式")
    tracking_no: str = Field(..., description="物流单号")
    shipping_fee: Decimal = Field(..., description="运费")


class OrderPayCaListItemSchema(BaseModel):
    """订单支付流水"""

    ca_no: str = Field(..., description="支付流水号")
    pay_amount: Decimal = Field(..., description="支付金额")
    pay_method_str: str = Field(..., description="支付方式")
    operator_info: str = Field(..., description="操作人信息")
    operator_time_str: str = Field(..., description="操作时间")
    operator_memo: str = Field(..., description="备注")


class OrderPaySchema(BaseModel):
    """订单支付"""

    order_id: int = Field(..., description="订单ID")
    pay_amount: Decimal = Field(..., description="支付金额")
    operator_memo: str = Field(..., description="备注")
    pay_method: int = Field(..., description="支付方式")


class OrderListByPatternItemSchema(BaseModel):
    """按版号查询关联订单列表项"""

    pk: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单编号")
    order_status: int = Field(..., description="订单状态")
    order_status_str: str = Field("", description="订单状态文本")
    receiver_name: str = Field("", description="收货人")
    receiver_phone: str = Field("", description="收货人电话")
    payable_amount: Decimal = Field(..., description="应付金额")
    paid_amount: Decimal = Field(..., description="实付金额")


class MobileOrderListItemSchema(BaseModel):
    """移动端订单列表项"""

    order_id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单编号")
    order_status: int = Field(..., description="订单状态")
    order_status_str: str = Field(..., description="订单状态文本")
    payable_amount: Decimal = Field(..., description="应付金额")
    receiver_company: str | None = Field(None, description="收货公司")
    main_images: list[str] = Field(default_factory=list, description="订单所有版式主图")
    create_time_str: str | None = Field(None, description="创建时间")


class OrderItemInfoSchema(BaseModel):
    """订单项明细"""

    item_id: int = Field(..., description="订单项ID")
    item_no: str = Field(..., description="订单项编号")
    pattern_code: str = Field(..., description="款号")
    main_image: str | None = Field(None, description="版式主图")
    color: str = Field(..., description="颜色")
    count: int = Field(..., description="数量")
    unit_price: Decimal = Field(..., description="单价")
    discount_price: Decimal = Field(..., description="优惠金额")
    total_unit: str = Field(..., description="单位")
    total: Decimal = Field(..., description="行合计")
    subtotal: Decimal = Field(..., description="行小计")
    memo: str | None = Field(None, description="备注")


class MobileOrderInfoSchema(BaseModel):
    """移动端订单详情"""

    order_id: int = Field(..., description="订单ID")
    order_no: str = Field(..., description="订单编号")
    order_type: int = Field(..., description="订单类型")
    order_type_str: str = Field(..., description="订单类型文本")
    order_status: int = Field(..., description="订单状态")
    order_status_str: str = Field(..., description="订单状态文本")
    pay_status: int = Field(..., description="支付状态")
    pay_status_str: str = Field(..., description="支付状态文本")
    ship_status: int = Field(..., description="发货状态")
    ship_status_str: str = Field(..., description="发货状态文本")
    total_amount: Decimal = Field(..., description="订单总金额")
    discount_amount: Decimal = Field(..., description="优惠金额")
    shipping_fee: Decimal = Field(..., description="运费")
    payable_amount: Decimal = Field(..., description="应付金额")
    paid_amount: Decimal = Field(..., description="实付金额")
    shipping_party: str | None = Field(None, description="发货方")
    shipping_party_company: str | None = Field(None, description="发货公司")
    shipping_party_phone: str | None = Field(None, description="发货电话")
    shipping_party_address: str | None = Field(None, description="发货地址")
    delivery_method: int = Field(..., description="配送方式")
    delivery_method_str: str = Field(..., description="配送方式文本")
    delivery_time: int | None = Field(None, description="配送时间")
    tracking_no: str | None = Field(None, description="物流单号")
    receiver_name: str | None = Field(None, description="收货人")
    receiver_phone: str | None = Field(None, description="收货电话")
    receiver_company: str | None = Field(None, description="收货公司")
    receiver_address: str | None = Field(None, description="收货地址")
    memo: str | None = Field(None, description="备注")
    create_time_str: str | None = Field(None, description="创建时间")
    items: list[OrderItemInfoSchema] = Field(..., description="订单项")


class OrderTimelineItemSchema(BaseModel):
    """订单日志"""

    item_title: str = Field(..., description="标题")
    item_user: str | None = Field(None, description="操作人")
    item_phone: str | None = Field(None, description="操作人电话")
    item_time: str | None = Field(None, description="操作时间")
    item_memo: str | None = Field(None, description="备注")


class OrderStatusActionSchema(BaseModel):
    """订单状态操作"""

    order_id: int = Field(..., description="订单ID")
    action: str = Field(..., description="动作标识")
    operator_memo: str | None = Field(None, description="操作备注")


class OrderActionSchema(BaseModel):
    """订单单步状态操作"""

    order_id: int = Field(..., description="订单ID")
    operator_memo: str | None = Field(None, description="操作备注")


class OrderStatusFlowItemSchema(BaseModel):
    status: int = Field(..., description="订单状态值")
    status_str: str = Field(..., description="订单状态文本")
    is_current: bool = Field(default=False, description="是否当前状态")


class OrderStatusBranchSchema(BaseModel):
    branch: str = Field(..., description="分支编码")
    branch_name: str = Field(..., description="分支名称")
    statuses: list[OrderStatusFlowItemSchema] = Field(default_factory=list, description="分支状态列表")


class OrderStatusAllFlowSchema(BaseModel):
    branches: list[OrderStatusBranchSchema] = Field(default_factory=list, description="订单状态分支列表")
