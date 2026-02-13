from typing import Any
from pydantic import BaseModel, Field


class ChoicesListItemSchema(BaseModel):
    
    label: str = Field(..., description="枚举的label")
    name: str = Field(..., description="枚举的名称")
    value: Any = Field(..., description="枚举的值")