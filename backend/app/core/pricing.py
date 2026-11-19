"""
Official and configurable model pricing tables.
Prices are stored as USD per 1 Million tokens (input and output) with effective dates.
"""
from typing import Dict, Any, Optional

DEFAULT_PRICING_TABLE = {
    # OpenAI (effective: 2024-2025 official pricing)
    "gpt-4o": {
        "provider": "openai",
        "input_price_per_1m": 2.50,
        "output_price_per_1m": 10.00,
        "effective_date": "2024-08-01",
        "currency": "USD"
    },
    "gpt-4o-mini": {
        "provider": "openai",
        "input_price_per_1m": 0.15,
        "output_price_per_1m": 0.60,
        "effective_date": "2024-08-01",
        "currency": "USD"
    },
    "gpt-4-turbo": {
        "provider": "openai",
        "input_price_per_1m": 10.00,
        "output_price_per_1m": 30.00,
        "effective_date": "2024-04-01",
        "currency": "USD"
    },
    "o1-preview": {
        "provider": "openai",
        "input_price_per_1m": 15.00,
        "output_price_per_1m": 60.00,
        "effective_date": "2024-09-12",
        "currency": "USD"
    },
    # Anthropic
    "claude-3-5-sonnet-20241022": {
        "provider": "anthropic",
        "input_price_per_1m": 3.00,
        "output_price_per_1m": 15.00,
        "effective_date": "2024-10-22",
        "currency": "USD"
    },
    "claude-3-5-haiku-20241022": {
        "provider": "anthropic",
        "input_price_per_1m": 0.80,
        "output_price_per_1m": 4.00,
        "effective_date": "2024-11-04",
        "currency": "USD"
    },
    "claude-3-opus-20240229": {
        "provider": "anthropic",
        "input_price_per_1m": 15.00,
        "output_price_per_1m": 75.00,
        "effective_date": "2024-03-01",
        "currency": "USD"
    },
    # Google Gemini
    "gemini-1.5-pro": {
        "provider": "gemini",
        "input_price_per_1m": 1.25,
        "output_price_per_1m": 5.00,
        "effective_date": "2024-09-01",
        "currency": "USD"
    },
    "gemini-1.5-flash": {
        "provider": "gemini",
        "input_price_per_1m": 0.075,
        "output_price_per_1m": 0.30,
        "effective_date": "2024-09-01",
        "currency": "USD"
    },
    "gemini-2.0-flash": {
        "provider": "gemini",
        "input_price_per_1m": 0.10,
        "output_price_per_1m": 0.40,
        "effective_date": "2025-01-15",
        "currency": "USD"
    },
    # Mock models (used for deterministic benchmarks and demo evaluations)
    "mock-gpt-4o": {
        "provider": "mock",
        "input_price_per_1m": 2.50,
        "output_price_per_1m": 10.00,
        "effective_date": "2024-08-01",
        "currency": "USD"
    },
    "mock-claude-3-5-sonnet": {
        "provider": "mock",
        "input_price_per_1m": 3.00,
        "output_price_per_1m": 15.00,
        "effective_date": "2024-10-22",
        "currency": "USD"
    },
    "mock-gemini-1.5-pro": {
        "provider": "mock",
        "input_price_per_1m": 1.25,
        "output_price_per_1m": 5.00,
        "effective_date": "2024-09-01",
        "currency": "USD"
    },
    "mock-fast-model": {
        "provider": "mock",
        "input_price_per_1m": 0.15,
        "output_price_per_1m": 0.60,
        "effective_date": "2024-08-01",
        "currency": "USD"
    }
}

def estimate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    custom_pricing: Optional[Dict[str, Any]] = None
) -> float:
    """
    Calculate estimated cost in USD based on input and output token counts.
    Returns calculated cost rounded to 6 decimal places.
    """
    pricing = None
    if custom_pricing and model_name in custom_pricing:
        pricing = custom_pricing[model_name]
    elif model_name in DEFAULT_PRICING_TABLE:
        pricing = DEFAULT_PRICING_TABLE[model_name]
    else:
        # Fallback to general average ($1.00 input / $3.00 output per 1M tokens)
        pricing = {
            "input_price_per_1m": 1.00,
            "output_price_per_1m": 3.00
        }
    
    input_cost = (input_tokens / 1_000_000.0) * pricing["input_price_per_1m"]
    output_cost = (output_tokens / 1_000_000.0) * pricing["output_price_per_1m"]
    return round(input_cost + output_cost, 6)
