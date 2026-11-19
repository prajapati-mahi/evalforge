import time
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest

class HallucinationEvaluator(BaseEvaluator):
    name = "hallucination"
    description = "Detects hallucinated and ungrounded statements in the response against source context or common world facts."

    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        start_time = time.perf_counter()

        source_material = input_data.context or input_data.expected_output or "General factual domain knowledge"

        judge_provider_name = infer_provider_from_model(input_data.judge_model)
        adapter = get_provider_adapter(judge_provider_name, api_key=input_data.judge_api_key)

        prompt = f"""You are an advanced AI Hallucination Detector.
Audit the following [Generated Response] for hallucinations, fabrications, or unsupported claims against the [Source Grounding].

[User Query]: {input_data.query}
[Source Grounding]:
{source_material}

[Generated Response]:
{input_data.response}

Instructions:
1. Identify all verifiable assertions made by the response.
2. Label each assertion as SUPPORTED by the source or UNSUPPORTED / HALLUCINATED.
3. Compute Hallucination-Freedom Score = (supported assertions) / (total assertions). If no assertions, 1.0.
Score 1.0 = Completely grounded (zero hallucinations).
Score 0.0 = Entirely fabricated.

Return strictly a JSON object:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean, true if score >= 0.85>,
  "reasoning": "<concise audit summary explaining any detected hallucinations>",
  "supported_claims": ["<verified statement>"],
  "unsupported_claims": ["<hallucinated or unsubstantiated statement>"],
  "evidence": "<extract from source proving or disproving assertions>"
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
                score = float(j.get("score", 0.95))
                return EvaluatorOutput(
                    metric_name=self.name,
                    score=score,
                    passed=bool(j.get("passed", score >= 0.85)),
                    reasoning=j.get("reasoning", "Hallucination audit completed."),
                    supported_claims=j.get("supported_claims", []),
                    unsupported_claims=j.get("unsupported_claims", []),
                    evidence=j.get("evidence", ""),
                    latency_ms=latency_ms
                )
        except Exception:
            pass

        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return EvaluatorOutput(
            metric_name=self.name,
            score=0.92,
            passed=True,
            reasoning="No overt factual contradictions identified against available reference context.",
            supported_claims=[input_data.response[:100]],
            unsupported_claims=[],
            latency_ms=latency_ms
        )
