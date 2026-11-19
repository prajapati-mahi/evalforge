from typing import Dict, Type, List, Optional
from app.evaluators.base import BaseEvaluator, EvaluatorInput, EvaluatorOutput
from app.evaluators.correctness import AnswerCorrectnessEvaluator
from app.evaluators.faithfulness import FaithfulnessEvaluator
from app.evaluators.context_precision import ContextPrecisionEvaluator
from app.evaluators.context_recall import ContextRecallEvaluator
from app.evaluators.relevance import ResponseRelevanceEvaluator
from app.evaluators.hallucination import HallucinationEvaluator

_EVALUATOR_REGISTRY: Dict[str, Type[BaseEvaluator]] = {
    "correctness": AnswerCorrectnessEvaluator,
    "faithfulness": FaithfulnessEvaluator,
    "context_precision": ContextPrecisionEvaluator,
    "context_recall": ContextRecallEvaluator,
    "response_relevance": ResponseRelevanceEvaluator,
    "hallucination": HallucinationEvaluator,
}

def get_evaluator(name: str) -> Optional[BaseEvaluator]:
    cls = _EVALUATOR_REGISTRY.get(name.lower())
    if cls:
        return cls()
    return None

def list_available_evaluators() -> List[Dict[str, str]]:
    return [
        {"name": k, "description": v.description}
        for k, v in _EVALUATOR_REGISTRY.items()
    ]

async def run_evaluators(
    metric_names: List[str],
    input_data: EvaluatorInput
) -> List[EvaluatorOutput]:
    """Execute requested evaluators concurrently or sequentially."""
    results: List[EvaluatorOutput] = []
    for name in metric_names:
        evaluator = get_evaluator(name)
        if evaluator:
            res = await evaluator.evaluate(input_data)
            results.append(res)
    return results
