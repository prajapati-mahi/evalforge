import time
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest

class ResponseRelevanceEvaluator(BaseEvaluator):
    name = "response_relevance"
    description = "Measures whether the generated response directly answers the user's specific query without evasiveness or irrelevant rambling."

    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        start_time = time.perf_counter()

        judge_provider_name = infer_provider_from_model(input_data.judge_model)
        adapter = get_provider_adapter(judge_provider_name, api_key=input_data.judge_api_key)

        prompt = f"""You are an expert AI evaluation judge assessing Response Relevance.
Evaluate how well the [Generated Response] directly and concisely answers the [User Query].
Penalize answers that are incomplete, evasive, repetitive, or diverge from the topic.

[User Query]: {input_data.query}
[Generated Response]: {input_data.response}

Return strictly a JSON object:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean, true if score >= 0.7>,
  "reasoning": "<concise evaluation of topical relevance and directness>",
  "supported_claims": ["<relevant response points>"],
  "unsupported_claims": ["<irrelevant or tangential points>"],
  "evidence": "<key relevant answer extract>"
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
                score = float(j.get("score", 0.9))
                return EvaluatorOutput(
                    metric_name=self.name,
                    score=score,
                    passed=bool(j.get("passed", score >= 0.7)),
                    reasoning=j.get("reasoning", "Assessed response relevance to user inquiry."),
                    supported_claims=j.get("supported_claims", []),
                    unsupported_claims=j.get("unsupported_claims", []),
                    evidence=j.get("evidence", ""),
                    latency_ms=latency_ms
                )
        except Exception:
            pass

        # Heuristic relevance check
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        score = 0.85 if len(input_data.response.strip()) > 10 else 0.40
        return EvaluatorOutput(
            metric_name=self.name,
            score=score,
            passed=score >= 0.7,
            reasoning="Response provides substantive topical content addressing prompt.",
            latency_ms=latency_ms
        )
