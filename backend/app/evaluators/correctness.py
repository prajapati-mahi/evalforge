import re
import string
import time
from typing import List, Set
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest

def normalize_text(text: str) -> str:
    """Lower text and remove punctuation, articles and extra whitespace."""
    def remove_articles(t):
        return re.sub(r"\b(a|an|the)\b", " ", t)

    def white_space_fix(t):
        return " ".join(t.split())

    def remove_punc(t):
        exclude = set(string.punctuation)
        return "".join(ch for ch in t if ch not in exclude)

    return white_space_fix(remove_articles(remove_punc(text.lower())))

def compute_f1(prediction: str, ground_truth: str) -> float:
    pred_tokens = normalize_text(prediction).split()
    truth_tokens = normalize_text(ground_truth).split()
    
    if not pred_tokens or not truth_tokens:
        return 1.0 if pred_tokens == truth_tokens else 0.0

    common: Set[str] = set(pred_tokens) & set(truth_tokens)
    num_same = sum(min(pred_tokens.count(w), truth_tokens.count(w)) for w in common)
    
    if num_same == 0:
        return 0.0
        
    precision = 1.0 * num_same / len(pred_tokens)
    recall = 1.0 * num_same / len(truth_tokens)
    f1 = (2 * precision * recall) / (precision + recall)
    return round(f1, 4)

class AnswerCorrectnessEvaluator(BaseEvaluator):
    name = "correctness"
    description = "Evaluates answer correctness against the expected ground truth using lexical, semantic, and judge methods."

    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        start_time = time.perf_counter()
        
        if not input_data.expected_output:
            return EvaluatorOutput(
                metric_name=self.name,
                score=1.0,
                passed=True,
                reasoning="No ground truth expected output provided; defaulting to neutral pass.",
                latency_ms=0.0
            )

        norm_pred = normalize_text(input_data.response)
        norm_truth = normalize_text(input_data.expected_output)

        # 1. Exact match check
        if norm_pred == norm_truth:
            return EvaluatorOutput(
                metric_name=self.name,
                score=1.0,
                passed=True,
                reasoning="Exact normalized match with ground truth answer.",
                supported_claims=[input_data.response],
                evidence=input_data.expected_output,
                latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2)
            )

        # 2. Token overlap / F1 score
        token_f1 = compute_f1(input_data.response, input_data.expected_output)

        # 3. If model is available and expected output is non-trivial, run LLM-as-a-judge
        judge_provider_name = infer_provider_from_model(input_data.judge_model)
        adapter = get_provider_adapter(judge_provider_name, api_key=input_data.judge_api_key)

        judge_prompt = f"""You are an expert AI evaluation judge assessing Answer Correctness.
Given:
[User Query]: {input_data.query}
[Expected Ground Truth]: {input_data.expected_output}
[Generated Model Response]: {input_data.response}

Analyze if the generated response accurately reflects the key factual points of the expected answer.
Output a valid JSON object matching this schema:
{{
  "score": <float between 0.0 and 1.0>,
  "passed": <boolean, true if score >= 0.7>,
  "reasoning": "<concise explanation>",
  "supported_claims": ["<claims verified against ground truth>"],
  "unsupported_claims": ["<inaccuracies or missing critical facts>"],
  "evidence": "<reference to expected output>"
}}
JSON:"""

        try:
            req = LLMRequest(
                prompt=judge_prompt,
                model_name=input_data.judge_model,
                temperature=0.0,
                json_mode=True,
                timeout=15.0
            )
            res = await adapter.generate(req)
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            if res.raw_json and "score" in res.raw_json:
                j = res.raw_json
                return EvaluatorOutput(
                    metric_name=self.name,
                    score=float(j.get("score", token_f1)),
                    passed=bool(j.get("passed", token_f1 >= 0.7)),
                    reasoning=j.get("reasoning", f"Evaluated with lexical F1: {token_f1}"),
                    supported_claims=j.get("supported_claims", []),
                    unsupported_claims=j.get("unsupported_claims", []),
                    evidence=j.get("evidence", input_data.expected_output),
                    latency_ms=latency_ms
                )
        except Exception:
            pass

        # Fallback to lexical F1
        latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        return EvaluatorOutput(
            metric_name=self.name,
            score=token_f1,
            passed=token_f1 >= 0.65,
            reasoning=f"Lexical token overlap F1 score: {token_f1:.2f}.",
            supported_claims=[input_data.response] if token_f1 >= 0.65 else [],
            unsupported_claims=[] if token_f1 >= 0.65 else [input_data.response],
            evidence=input_data.expected_output,
            latency_ms=latency_ms
        )
