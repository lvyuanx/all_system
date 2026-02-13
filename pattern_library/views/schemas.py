
from pydantic import BaseModel, Field


class PatternListItemSchema(BaseModel):
    
    main_image: str = Field(..., description="主图")
    pattern_name: str = Field(..., description="名称")
    pattern_code: str = Field(..., description="版号")
    pattern_memo: str = Field(..., description="备注")