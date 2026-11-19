import asyncio
import json
import time
from typing import Dict, Any, Optional
import httpx
from app.providers.base import BaseProviderAdapter, LLMRequest, LLMResponse

class OpenAIAdapter(BaseProviderAdapter):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.base_url = "https://api.openai.com/v1"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                text="",
                error="OpenAI API key is missing. Please configure your OpenAI credentials in Provider Settings.",
                provider="openai",
                model_name=request.model_name
            )

        start_time = time.perf_counter()
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if request.system_instruction:
            messages.append({"role": "system", "content": request.system_instruction})
        messages.append({"role": "user", "content": request.prompt})

        payload = {
            "model": request.model_name,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens
        }

        if request.json_mode:
            payload["response_format"] = {"type": "json_object"}

        # Retry loop with exponential backoff
        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=request.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )

                if response.status_code == 200:
                    data = response.json()
                    choice = data["choices"][0]
                    content = choice["message"]["content"]
                    usage = data.get("usage", {})
                    
                    input_tokens = usage.get("prompt_tokens", 0)
                    output_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", input_tokens + output_tokens)
                    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

                    raw_json = None
                    if request.json_mode:
                        try:
                            raw_json = json.loads(content)
                        except Exception:
                            raw_json = None

                    return LLMResponse(
                        text=content,
                        raw_json=raw_json,
                        input_tokens=input_tokens,
                        output_tokens=output_tokens,
                        total_tokens=total_tokens,
                        latency_ms=latency_ms,
                        provider="openai",
                        model_name=request.model_name,
                        finish_reason=choice.get("finish_reason", "stop")
                    )

                elif response.status_code == 429:
                    # Rate limit - backoff
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    else:
                        return LLMResponse(
                            text="",
                            error=f"OpenAI rate limit exceeded: {response.text}",
                            provider="openai",
                            model_name=request.model_name
                        )
                else:
                    return LLMResponse(
                        text="",
                        error=f"OpenAI API error ({response.status_code}): {response.text}",
                        provider="openai",
                        model_name=request.model_name
                    )

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return LLMResponse(
                    text="",
                    error=f"OpenAI request timed out after {request.timeout}s",
                    provider="openai",
                    model_name=request.model_name
                )
            except Exception as e:
                return LLMResponse(
                    text="",
                    error=f"Unexpected error communicating with OpenAI: {str(e)}",
                    provider="openai",
                    model_name=request.model_name
                )

        return LLMResponse(text="", error="Exhausted retries", provider="openai", model_name=request.model_name)

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "message": "API key not provided."}
        try:
            req = LLMRequest(prompt="ping", model_name="gpt-4o-mini", max_tokens=5, timeout=10.0)
            res = await self.generate(req)
            if res.error:
                return {"status": "error", "message": res.error}
            return {"status": "connected", "provider": "openai", "message": "Authentication successful."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
