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
    receiver_company: str = Field(description="收货人公司")
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

