from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import time

class LLMRequest(BaseModel):
    prompt: str
    system_instruction: Optional[str] = None
    model_name: str
    temperature: float = 0.7
    max_tokens: int = 1024
    json_mode: bool = False
    timeout: float = 30.0
    variables: Dict[str, Any] = Field(default_factory=dict)

class LLMResponse(BaseModel):
    text: str
    raw_json: Optional[Dict[str, Any]] = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    provider: str
    model_name: str
    is_mock: bool = False
    error: Optional[str] = None
    finish_reason: Optional[str] = "stop"

class BaseProviderAdapter(ABC):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Execute a text generation call with retries and timeout."""
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test whether the provided API key is valid and working."""
        pass
