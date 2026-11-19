from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.provider import ModelProviderKey, ModelPricing
from app.models.user import User
from app.schemas.provider import (
    ProviderKeyCreate, ProviderKeyResponse,
    ModelPricingCreate, ModelPricingResponse
)
from app.api.deps import get_current_user
from app.providers.factory import get_provider_adapter
from app.core.pricing import DEFAULT_PRICING_TABLE

router = APIRouter(prefix="/providers", tags=["Providers"])

@router.get("", response_model=List[ProviderKeyResponse])
def list_configured_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    keys = (
        db.query(ModelProviderKey)
        .filter(ModelProviderKey.user_id == current_user.id)
        .all()
    )
    return keys

@router.post("/configure", response_model=ProviderKeyResponse)
def configure_provider(
    key_in: ProviderKeyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Mask key prefix (e.g. sk-pro...9qW)
    raw = key_in.api_key.strip()
    prefix = f"{raw[:6]}...{raw[-4:]}" if len(raw) > 10 else "configured"

    existing = (
        db.query(ModelProviderKey)
        .filter(
            ModelProviderKey.user_id == current_user.id,
            ModelProviderKey.provider_name == key_in.provider_name.lower()
        )
        .first()
    )

    if existing:
        existing.key_prefix = prefix
        existing.encrypted_key = raw  # In production, encrypt using AES-256 GCM
        existing.is_active = True
        existing.is_default = key_in.is_default or False
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_key = ModelProviderKey(
            user_id=current_user.id,
            provider_name=key_in.provider_name.lower(),
            key_prefix=prefix,
            encrypted_key=raw,
            is_active=True,
            is_default=key_in.is_default or False
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        return new_key

@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider_key(
    key_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    key = db.query(ModelProviderKey).filter(ModelProviderKey.id == key_id, ModelProviderKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="Provider key configuration not found.")
    db.delete(key)
    db.commit()
    return None

@router.post("/test/{provider_name}")
async def test_provider_connection(
    provider_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Test connection using user's configured key or environment credentials."""
    key_record = (
        db.query(ModelProviderKey)
        .filter(
            ModelProviderKey.user_id == current_user.id,
            ModelProviderKey.provider_name == provider_name.lower()
        )
        .first()
    )
    api_key = key_record.encrypted_key if key_record else None
    adapter = get_provider_adapter(provider_name, api_key=api_key)
    result = await adapter.test_connection()
    return result

@router.get("/pricing", response_model=List[ModelPricingResponse])
def get_model_pricing(db: Session = Depends(get_db)):
    # Check DB custom pricing first, combined with default pricing
    db_pricings = db.query(ModelPricing).all()
    results = [ModelPricingResponse.model_validate(p) for p in db_pricings]

    existing_names = {p.model_name for p in db_pricings}
    for model_name, info in DEFAULT_PRICING_TABLE.items():
        if model_name not in existing_names:
            results.append(ModelPricingResponse(
                id=0,
                provider=info["provider"],
                model_name=model_name,
                input_price_per_1m=info["input_price_per_1m"],
                output_price_per_1m=info["output_price_per_1m"],
                effective_date=info["effective_date"],
                is_custom=False,
                created_at="2024-10-01T00:00:00"
            ))
    return results
