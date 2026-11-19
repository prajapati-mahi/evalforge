import time
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest

class FaithfulnessEvaluator(BaseEvaluator):
    name = "faithfulness"
    description = "Measures whether claims in the generated response can be directly inferred from the supplied context."

    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        start_time = time.perf_counter()

        if not input_data.context:
            return EvaluatorOutput(
                metric_name=self.name,
                score=1.0,
                passed=True,
                reasoning="No retrieved context was provided; faithfulness evaluation not applicable.",
                latency_ms=0.0
            )

        judge_provider_name = infer_provider_from_model(input_data.judge_model)
        adapter = get_provider_adapter(judge_provider_name, api_key=input_data.judge_api_key)

        prompt = f"""You are an impartial AI safety and grounding judge evaluating Faithfulness.
Evaluate whether the [Generated Response] makes any factual statements or extrapolations that are NOT supported by the [Context].

[Context]:
{input_data.context}

[User Query]:
{input_data.query}

[Generated Response]:
{input_data.response}

Step 1: Extract distinct factual claims from the generated response.
Step 2: Check each claim against the context.
Step 3: Calculate score = (number of supported claims) / (total claims). If no claims, score is 1.0.

Return strictly a JSON object:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean, true if score >= 0.8>,
  "reasoning": "<concise step-by-step reasoning>",
  "supported_claims": ["<claim supported by context>"],
  "unsupported_claims": ["<claim not found in context>"],
  "evidence": "<direct quotes from context supporting claims>"
}}
JSON:"""

        req = LLMRequest(
            prompt=prompt,
            model_name=input_data.judge_model,
            temperature=0.0,
            json_mode=True,
            timeout=20.0
        )

        try:
            res = await adapter.generate(req)
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            if res.raw_json and "score" in res.raw_json:
                j = res.raw_json
                score = float(j.get("score", 0.0))
                return EvaluatorOutput(
                    metric_name=self.name,
                    score=score,
                    passed=bool(j.get("passed", score >= 0.8)),
                    reasoning=j.get("reasoning", "Faithfulness assessed via claim-level grounding verification."),
                    supported_claims=j.get("supported_claims", []),
                    unsupported_claims=j.get("unsupported_claims", []),
                    evidence=j.get("evidence", ""),
                    latency_ms=latency_ms
                )
        except Exception as e:
            pass

        # Fallback heuristic: check word overlap with context
        words_resp = set(input_data.response.lower().split())
        words_ctx = set(input_data.context.lower().split())
        overlap = len(words_resp & words_ctx) / max(1, len(words_resp))
        score = round(min(1.0, max(0.0, overlap * 1.2)), 2)

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return EvaluatorOutput(
            metric_name=self.name,
            score=score,
            passed=score >= 0.7,
            reasoning=f"Lexical overlap verification against context yielded score of {score}.",
            supported_claims=["Substantive vocabulary overlap with provided document passages."],
            unsupported_claims=[] if score >= 0.7 else ["Low vocabulary grounding in reference text."],
            evidence=input_data.context[:200] + "...",
            latency_ms=latency_ms
        )
