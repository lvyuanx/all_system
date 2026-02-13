

from pydantic import BaseModel, Field


class ClientAddressListItemSchema(BaseModel):
    
    receiver_name: str = Field(..., description="发货方")
    receiver_phone: str = Field(..., description="发货方电话")
    receiver_address: str = Field(..., description="发货方地址")
    receiver_company: str = Field(..., description="发货方公司")
    
    
    