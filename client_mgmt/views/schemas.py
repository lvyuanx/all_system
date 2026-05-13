

from pydantic import BaseModel, Field


class ClientAddressListItemSchema(BaseModel):
    
    receiver_name: str = Field(..., description="发货方")
    receiver_phone: str = Field(..., description="发货方电话")
    receiver_address: str = Field(..., description="发货方地址")
    receiver_company: str = Field(..., description="发货方公司")


class MobileClientListItemSchema(BaseModel):
    client_id: int = Field(..., description="客户ID")
    client_name: str = Field(..., description="客户名称")
    client_phone: str | None = Field(None, description="客户电话")
    client_sex: str = Field(..., description="性别编码")
    client_sex_str: str = Field(..., description="性别文本")
    client_age: int | None = Field(None, description="客户年龄")
    settlement_method: str = Field(..., description="结款方式编码")
    settlement_method_str: str = Field(..., description="结款方式文本")
    company_name: str | None = Field(None, description="公司名称")
    company_phone: str | None = Field(None, description="公司电话")
    company_logo: str | None = Field(None, description="公司logo")
    full_address: str = Field(..., description="完整地址")
    total_amount: float = Field(..., description="历史下单总金额")
    total_arrears: float = Field(..., description="欠款总额")
    total_order_count: int = Field(..., description="历史下单总数")
    total_end_order_count: int = Field(..., description="历史结束订单数")
    unfinished_order_total: int = Field(..., description="未结束订单数")
    site_names: list[str] = Field(default_factory=list, description="所属站点")


class MobileClientInfoSchema(BaseModel):
    client_id: int = Field(..., description="客户ID")
    client_name: str = Field(..., description="客户名称")
    client_phone: str | None = Field(None, description="客户电话")
    client_sex: str = Field(..., description="性别编码")
    client_sex_str: str = Field(..., description="性别文本")
    client_age: int | None = Field(None, description="客户年龄")
    settlement_method: str = Field(..., description="结款方式编码")
    settlement_method_str: str = Field(..., description="结款方式文本")
    company_name: str | None = Field(None, description="公司名称")
    company_phone: str | None = Field(None, description="公司电话")
    company_logo: str | None = Field(None, description="公司logo")
    address_province: str | None = Field(None, description="省")
    address_city: str | None = Field(None, description="市")
    address_district: str | None = Field(None, description="区")
    address_detail: str | None = Field(None, description="详细地址")
    full_address: str = Field(..., description="完整地址")
    total_amount: float = Field(..., description="历史下单总金额")
    total_arrears: float = Field(..., description="欠款总额")
    total_order_count: int = Field(..., description="历史下单总数")
    total_end_order_count: int = Field(..., description="历史结束订单数")
    unfinished_order_total: int = Field(..., description="未结束订单数")
    site_names: list[str] = Field(default_factory=list, description="所属站点")
    
    
    
