from pydantic import BaseModel, Field


class PatternListItemSchema(BaseModel):
    
    main_image: str = Field(..., description="主图")
    pattern_code: str = Field(..., description="版号")
    pattern_memo: str | None = Field(None, description="备注")