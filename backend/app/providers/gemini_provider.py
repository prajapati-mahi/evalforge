import asyncio
import json
import time
from typing import Dict, Any, Optional
import httpx
from app.providers.base import BaseProviderAdapter, LLMRequest, LLMResponse

class GeminiAdapter(BaseProviderAdapter):
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    async def generate(self, request: LLMRequest) -> LLMResponse:
        if not self.api_key:
            return LLMResponse(
                text="",
                error="Google Gemini API key is missing. Please configure your Gemini API key in Provider Settings.",
                provider="gemini",
                model_name=request.model_name
            )

        start_time = time.perf_counter()
        endpoint = f"{self.base_url}/{request.model_name}:generateContent?key={self.api_key}"

        contents = [{"role": "user", "parts": [{"text": request.prompt}]}]
        generation_config: Dict[str, Any] = {
            "temperature": request.temperature,
            "maxOutputTokens": request.max_tokens,
        }

        if request.json_mode:
            generation_config["responseMimeType"] = "application/json"

        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": generation_config
        }

        if request.system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": request.system_instruction}]
            }

        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=request.timeout) as client:
                    response = await client.post(endpoint, json=payload)

                if response.status_code == 200:
                    data = response.json()
                    candidates = data.get("candidates", [])
                    if not candidates:
                        return LLMResponse(
                            text="",
                            error="Gemini returned no candidates.",
                            provider="gemini",
                            model_name=request.model_name
                        )

                    parts = candidates[0].get("content", {}).get("parts", [])
                    text = "".join([p.get("text", "") for p in parts])
                    
                    usage = data.get("usageMetadata", {})
                    input_tokens = usage.get("promptTokenCount", 0)
                    output_tokens = usage.get("candidatesTokenCount", 0)
                    total_tokens = usage.get("totalTokenCount", input_tokens + output_tokens)
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
                        provider="gemini",
                        model_name=request.model_name,
                        finish_reason=candidates[0].get("finishReason", "STOP")
                    )

                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(backoff)
                        backoff *= 2
                        continue
                    return LLMResponse(
                        text="",
                        error=f"Gemini quota / rate limit exceeded: {response.text}",
                        provider="gemini",
                        model_name=request.model_name
                    )
                else:
                    return LLMResponse(
                        text="",
                        error=f"Gemini API error ({response.status_code}): {response.text}",
                        provider="gemini",
                        model_name=request.model_name
                    )

            except httpx.TimeoutException:
                if attempt < max_retries - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 2
                    continue
                return LLMResponse(
                    text="",
                    error=f"Gemini request timed out after {request.timeout}s",
                    provider="gemini",
                    model_name=request.model_name
                )
            except Exception as e:
                return LLMResponse(
                    text="",
                    error=f"Unexpected error communicating with Gemini: {str(e)}",
                    provider="gemini",
                    model_name=request.model_name
                )

        return LLMResponse(text="", error="Exhausted retries", provider="gemini", model_name=request.model_name)

    async def test_connection(self) -> Dict[str, Any]:
        if not self.api_key:
            return {"status": "error", "message": "API key not provided."}
        try:
            req = LLMRequest(prompt="ping", model_name="gemini-1.5-flash", max_tokens=5, timeout=10.0)
            res = await self.generate(req)
            if res.error:
                return {"status": "error", "message": res.error}
            return {"status": "connected", "provider": "gemini", "message": "Authentication successful."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
