import asyncio
import json
import time
from typing import Dict, Any, Optional
import httpx
from app.providers.base import BaseProviderAdapter, LLMRequest, LLMResponse

class AnthropicAdapter(BaseProviderAdapter):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.base_url = "https://api.anthropic.com/v1"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                text="",
                error="Anthropic API key is missing. Please configure Anthropic credentials in Provider Settings.",
                provider="anthropic",
                model_name=request.model_name
            )

        start_time = time.perf_counter()
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        payload: Dict[str, Any] = {
            "model": request.model_name,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "messages": [{"role": "user", "content": request.prompt}]
        }

        if request.system_instruction:
            payload["system"] = request.system_instruction

        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=request.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/messages",
                        headers=headers,
                        json=payload
                    )

                if response.status_code == 200:
                    data = response.json()
                    content_blocks = data.get("content", [])
                    text = "".join([c.get("text", "") for c in content_blocks if c.get("type") == "text"])
                    usage = data.get("usage", {})
                    
                    input_tokens = usage.get("input_tokens", 0)
                    output_tokens = usage.get("output_tokens", 0)
                    total_tokens = input_tokens + output_tokens
                    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

                    raw_json = None
                    if request.json_mode:
                        try:
                            raw_json = json.loads(text)
                        except Exception:
                            raw_json = None

                    return LLMResponse(
                        text=text,
                        raw_json=raw_json,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        latency_ms=latency_ms,
                        provider="anthropic",
                        model_name=request.model_name,
                        finish_reason=data.get("stop_reason", "end_turn")
                    )

                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    return LLMResponse(
                        text="",
                        error=f"Anthropic rate limit: {response.text}",
                        provider="anthropic",
                        model_name=request.model_name
                    )
                else:
                    return LLMResponse(
                        text="",
                        error=f"Anthropic API error ({response.status_code}): {response.text}",
                        provider="anthropic",
                        model_name=request.model_name
                    )

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return LLMResponse(
                    text="",
                    error=f"Anthropic request timed out after {request.timeout}s",
                    provider="anthropic",
                    model_name=request.model_name
                )
            except Exception as e:
                return LLMResponse(
                    text="",
                    error=f"Unexpected error communicating with Anthropic: {str(e)}",
                    provider="anthropic",
                    model_name=request.model_name
                )

        return LLMResponse(text="", error="Exhausted retries", provider="anthropic", model_name=request.model_name)

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "message": "API key not provided."}
        try:
            req = LLMRequest(prompt="ping", model_name="claude-3-5-haiku-20241022", max_tokens=5, timeout=10.0)
            res = await self.generate(req)
            if res.error:
                return {"status": "error", "message": res.error}
            return {"status": "connected", "provider": "anthropic", "message": "Authentication successful."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
