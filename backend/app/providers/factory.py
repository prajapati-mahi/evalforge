from typing import Optional, Dict
from app.providers.base import BaseProviderAdapter
from app.providers.mock_provider import MockProviderAdapter
from app.providers.openai_provider import OpenAIAdapter
from app.providers.anthropic_provider import AnthropicAdapter
from app.providers.gemini_provider import GeminiAdapter
from app.core.config import settings

def get_provider_adapter(
    provider_name: str,
    api_key: Optional[str] = None
) -> BaseProviderAdapter:
    """
    Factory to retrieve an instantiated provider adapter.
    Falls back to environment variables if no user-supplied key is passed.
    """
    provider_name_lower = provider_name.lower()
    
    if provider_name_lower == "mock" or provider_name_lower.startswith("mock"):
        return MockProviderAdapter()
    
    elif provider_name_lower == "openai":
        key = api_key or settings.OPENAI_API_KEY
        return OpenAIAdapter(api_key=key)
        
    elif provider_name_lower == "anthropic":
        key = api_key or settings.ANTHROPIC_API_KEY
        return AnthropicAdapter(api_key=key)
        
    elif provider_name_lower in ("gemini", "google"):
        key = api_key or settings.GEMINI_API_KEY
        return GeminiAdapter(api_key=key)
        
    else:
        # Default fallback to Mock
        return MockProviderAdapter()

def infer_provider_from_model(model_name: str) -> str:
    m = model_name.lower()
    if m.startswith("mock"):
        return "mock"
    if "gpt" in m or "o1" in m or "text-embedding" in m:
        return "openai"
    if "claude" in m:
        return "anthropic"
    if "gemini" in m:
        return "gemini"
    return "mock"
