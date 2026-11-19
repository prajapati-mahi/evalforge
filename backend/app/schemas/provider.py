from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProviderKeyCreate(BaseModel):
    provider_name: str  # openai, anthropic, gemini, mock
    api_key: str
    is_default: Optional[bool] = False

class ProviderKeyResponse(BaseModel):
    id: int
    provider_name: str
    key_prefix: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ModelPricingBase(BaseModel):
    provider: str
    model_name: str
    input_price_per_1m: float
    output_price_per_1m: float
    effective_date: str = "2024-10-01"

class ModelPricingCreate(ModelPricingBase):
    pass

class ModelPricingResponse(ModelPricingBase):
    id: int
    is_custom: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
