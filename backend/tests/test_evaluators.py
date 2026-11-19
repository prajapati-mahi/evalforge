import pytest
import asyncio
from app.evaluators.base import EvaluatorInput
from app.evaluators.correctness import AnswerCorrectnessEvaluator, normalize_text, compute_f1
from app.evaluators.faithfulness import FaithfulnessEvaluator
from app.evaluators.context_precision import ContextPrecisionEvaluator
from app.evaluators.context_recall import ContextRecallEvaluator
from app.evaluators.hallucination import HallucinationEvaluator

@pytest.mark.asyncio
async def test_answer_correctness_exact_match():
    evaluator = AnswerCorrectnessEvaluator()
    inp = EvaluatorInput(
        query="What is Paris?",
        response="Capital of France.",
        expected_output="Capital of France."
    )
    res = await evaluator.evaluate(inp)
    assert res.score == 1.0
    assert res.passed is True
    assert "Exact" in res.reasoning

@pytest.mark.asyncio
async def test_answer_correctness_f1():
    f1 = compute_f1("The quick brown fox jumps over the lazy dog", "quick brown fox lazy dog")
    assert f1 > 0.7

@pytest.mark.asyncio
async def test_faithfulness_evaluator():
    evaluator = FaithfulnessEvaluator()
    inp = EvaluatorInput(
        query="What does RAG do?",
        response="RAG retrieves relevant documents from an external knowledge repository.",
        context="Retrieval-Augmented Generation (RAG) is an architecture that retrieves relevant documents from external knowledge bases.",
        judge_model="mock-gpt-4o"
    )
    res = await evaluator.evaluate(inp)
    assert res.score >= 0.7
    assert res.passed is True
    assert len(res.supported_claims) > 0

@pytest.mark.asyncio
async def test_hallucination_evaluator():
    evaluator = HallucinationEvaluator()
    inp = EvaluatorInput(
        query="Tell me about Apple sales",
        response="Apple sales were $383 billion in 2023.",
        context="Apple recorded net sales of $383 billion in fiscal 2023.",
        judge_model="mock-gpt-4o"
    )
    res = await evaluator.evaluate(inp)
    assert res.score >= 0.8
    assert res.passed is True
