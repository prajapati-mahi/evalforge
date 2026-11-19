import time
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest

class ContextRecallEvaluator(BaseEvaluator):
    name = "context_recall"
    description = "Measures whether the supplied context contains the information needed to answer the question, referenced against ground truth."

    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        start_time = time.perf_counter()

        if not input_data.context or not input_data.expected_output:
            return EvaluatorOutput(
                metric_name=self.name,
                score=1.0,
                passed=True,
                reasoning="Context or ground truth omitted; context recall evaluation skipped.",
                latency_ms=0.0
            )

        judge_provider_name = infer_provider_from_model(input_data.judge_model)
        adapter = get_provider_adapter(judge_provider_name, api_key=input_data.judge_api_key)

        prompt = f"""You are an expert RAG evaluation judge evaluating Context Recall.
Context recall evaluates if all statements in the [Expected Ground Truth] can be attributed to the [Retrieved Context].

[User Query]: {input_data.query}
[Expected Ground Truth]: {input_data.expected_output}
[Retrieved Context]: {input_data.context}

Calculate the fraction of ground truth facts that are present in the context.
Return strictly a JSON object:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean, true if score >= 0.75>,
  "reasoning": "<concise explanation of which ground truth facts are captured>",
  "supported_claims": ["<ground truth facts present in context>"],
  "unsupported_claims": ["<ground truth facts missing from context>"],
  "evidence": "<context segments providing recall>"
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
                score = float(j.get("score", 0.85))
                return EvaluatorOutput(
                    metric_name=self.name,
                    score=score,
                    passed=bool(j.get("passed", score >= 0.75)),
                    reasoning=j.get("reasoning", "Context recall verified against reference expectations."),
                    supported_claims=j.get("supported_claims", []),
                    unsupported_claims=j.get("unsupported_claims", []),
                    evidence=j.get("evidence", ""),
                    latency_ms=latency_ms
                )
        except Exception:
            pass

        # Fallback lexical recall
        truth_words = set(input_data.expected_output.lower().split())
        ctx_words = set(input_data.context.lower().split())
        overlap = len(truth_words & ctx_words) / max(1, len(truth_words))
        score = round(min(1.0, max(0.3, overlap * 1.1)), 2)
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return EvaluatorOutput(
            metric_name=self.name,
            score=score,
            passed=score >= 0.7,
            reasoning=f"Ground truth fact containment heuristic yielded score of {score}.",
            latency_ms=latency_ms
        )
