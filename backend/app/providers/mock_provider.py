import asyncio
import json
import hashlib
import time
from typing import Dict, Any, Optional
from app.providers.base import BaseProviderAdapter, LLMRequest, LLMResponse

class MockProviderAdapter(BaseProviderAdapter):
    """
    High-fidelity deterministic Mock provider for local development, demonstration,
    and fast CI/CD test runs without external API dependencies.
    """

    async def generate(self, request: LLMRequest) -> LLMResponse:
        start_time = time.perf_counter()
        
        # Simulate realistic async network processing time (20ms - 80ms)
        await asyncio.sleep(0.04)
        
        prompt_hash = hashlib.md5(request.prompt.encode("utf-8")).hexdigest()
        hash_val = int(prompt_hash[:4], 16)
        
        # Calculate realistic token lengths
        input_tokens = max(12, len(request.prompt.split()) + (len(request.system_instruction.split()) if request.system_instruction else 0))
        
        if request.json_mode or "LLM-as-a-judge" in request.prompt or "JSON" in request.prompt:
            # Deterministic evaluation output
            score = round(0.70 + (hash_val % 30) / 100.0, 2)
            if "fail" in request.prompt.lower() or "incorrect" in request.prompt.lower():
                score = round(0.20 + (hash_val % 25) / 100.0, 2)
                
            passed = score >= 0.70
            supported = ["Generated claims align with retrieved premise in context."]
            unsupported = [] if passed else ["Extraneous claim not verified by primary source context."]
            
            raw_data = {
                "score": score,
                "passed": passed,
                "reasoning": f"Automated deterministic evaluation score {score}. The model response " + 
                             ("faithfully adheres to context boundaries." if passed else "demonstrates minor ungrounded extrapolation."),
                "supported_claims": supported,
                "unsupported_claims": unsupported,
                "evidence": "Verification against supplied contextual chunks and reference."
            }
            text_output = json.dumps(raw_data)
            output_tokens = len(text_output.split())
        else:
            # Regular text completion
            if "capital of france" in request.prompt.lower():
                text_output = "The capital of France is Paris. It is renowned for its art, fashion, gastronomy, and cultural heritage."
            elif "rag" in request.prompt.lower():
                text_output = "Retrieval-Augmented Generation (RAG) optimizes LLM outputs by referencing an authoritative knowledge base outside of its training data before generating a response."
            else:
                text_output = f"[Deterministic Mock Output for {request.model_name}]: Based on the provided inquiry, the system recommends systematic benchmarking across accuracy, latency, and context adherence."
            
            output_tokens = len(text_output.split())
            raw_data = None

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        
        return LLMResponse(
            text=text_output,
            raw_json=raw_data,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            latency_ms=latency_ms,
            provider="mock",
            model_name=request.model_name,
            is_mock=True,
            finish_reason="stop"
        )

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "status": "connected",
            "provider": "mock",
            "message": "Mock Provider is operational. Zero API credentials required."
        }
