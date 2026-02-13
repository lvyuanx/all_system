

from pydantic import BaseModel, Field


class SiteAddressListItemSchema(BaseModel):
    
    shipping_party: str = Field(..., description="发货方")
    shipping_party_phone: str = Field(..., description="发货方电话")
    shipping_party_address: str = Field(..., description="发货方地址")
    shipping_party_company: str = Field(..., description="发货方公司")
    
    
    