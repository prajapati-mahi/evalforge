import re
from typing import Any, Dict

# Regex patterns matching potential API keys and secrets
SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9_-]{20,}",
    r"AIza[0-9A-Za-z-_]{35}",
    r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"ghp_[0-9a-zA-Z]{36}",
]

def redact_secrets(text: str) -> str:
    """Redact sensitive API keys, tokens, and passwords from logged traces."""
    if not text or not isinstance(text, str):
        return text
    
    redacted = text
    for pat in SECRET_PATTERNS:
        redacted = re.sub(pat, "[REDACTED_SECRET]", redacted, flags=re.IGNORECASE)
    return redacted

def sanitize_payload(payload: Any) -> Any:
    """Recursively sanitize dicts and strings."""
    if isinstance(payload, str):
        return redact_secrets(payload)
    elif isinstance(payload, dict):
        return {k: sanitize_payload(v) for k, v in payload.items()}
    elif isinstance(payload, list):
        return [sanitize_payload(item) for item in payload]
    return payload
