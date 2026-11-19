from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class ModelProviderKey(Base):
    __tablename__ = "model_provider_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    provider_name = Column(String(50), nullable=False)  # openai, anthropic, gemini, mock
    # Encrypted/masked storage: never return raw key to frontend
    key_prefix = Column(String(20), nullable=True)  # e.g. "sk-proj...7xQ"
    encrypted_key = Column(String(512), nullable=False)
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="api_credentials")

class ModelPricing(Base):
    __tablename__ = "model_pricing"

    id = Column(Integer, primary_key=True, index=True)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), unique=True, index=True, nullable=False)
    input_price_per_1m = Column(Float, nullable=False)
    output_price_per_1m = Column(Float, nullable=False)
    effective_date = Column(String(50), default="2024-10-01")
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
