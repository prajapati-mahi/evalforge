import time
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest

class ContextPrecisionEvaluator(BaseEvaluator):
    name = "context_precision"
    description = "Measures whether the retrieved context passages are relevant and focused on answering the query."

    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        start_time = time.perf_counter()

        if not input_data.context:
            return EvaluatorOutput(
                metric_name=self.name,
                score=1.0,
                passed=True,
                reasoning="No context provided for precision calculation.",
                latency_ms=0.0
            )

        judge_provider_name = infer_provider_from_model(input_data.judge_model)
        adapter = get_provider_adapter(judge_provider_name, api_key=input_data.judge_api_key)

        prompt = f"""You are an expert RAG evaluation judge evaluating Context Precision.
Context precision evaluates whether the provided context contains relevant information needed to answer the question without irrelevant noise.

[User Query]: {input_data.query}
[Expected Answer]: {input_data.expected_output or 'N/A'}
[Retrieved Context]: {input_data.context}

Analyze the proportion of the retrieved context that directly informs the answer to the query.
Return strictly a JSON object:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean, true if score >= 0.7>,
  "reasoning": "<concise explanation of context relevance>",
  "supported_claims": ["<relevant segments>"],
  "unsupported_claims": ["<distractor / irrelevant segments>"],
  "evidence": "<most relevant context snippet>"
}}
JSON:"""

        req = LLMRequest(
            prompt=prompt,
            model_name=input_data.judge_model,
            temperature=0.0,
            json_mode=True,
            timeout=15.0
        )

        try:
            res = await adapter.generate(req)
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            if res.raw_json and "score" in res.raw_json:
                j = res.raw_json
                score = float(j.get("score", 0.8))
                return EvaluatorOutput(
                    metric_name=self.name,
                    score=score,
                    passed=bool(j.get("passed", score >= 0.7)),
                    reasoning=j.get("reasoning", "Context precision measured via prompt-context relevance."),
                    supported_claims=j.get("supported_claims", []),
                    unsupported_claims=j.get("unsupported_claims", []),
                    evidence=j.get("evidence", ""),
                    latency_ms=latency_ms
                )
        except Exception:
            pass

        # Heuristic fallback based on query terms appearing in context
        query_words = set(input_data.query.lower().split())
        ctx_words = set(input_data.context.lower().split())
        found = len(query_words & ctx_words)
        score = round(min(1.0, max(0.4, found / max(1, len(query_words)))), 2)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return EvaluatorOutput(
            metric_name=self.name,
            score=score,
            passed=score >= 0.65,
            reasoning=f"Keyword presence ratio in context indicated precision of {score}.",
            evidence=input_data.context[:150],
            latency_ms=latency_ms
        )
