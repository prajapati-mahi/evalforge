from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.evaluation import EvaluationResult
from app.models.user import User
from app.schemas.evaluation import (
    SingleEvalRequest, EvaluationResultResponse, HumanReviewUpdate
)
from app.api.deps import get_current_user
from app.evaluators.base import EvaluatorInput
from app.evaluators.registry import get_evaluator

router = APIRouter(prefix="/evaluations", tags=["Evaluations"])

@router.post("/run")
async def run_single_evaluation(
    req: SingleEvalRequest,
    current_user: User = Depends(get_current_user)
):
    """Interactively run a metric evaluator on a query and response."""
    evaluator = get_evaluator(req.metric_name)
    if not evaluator:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown evaluator '{req.metric_name}'."
        )

    eval_input = EvaluatorInput(
        query=req.query,
        response=req.response,
        expected_output=req.expected_output,
        context=req.context,
        judge_model=req.judge_model or "mock-gpt-4o"
    )

    result = await evaluator.evaluate(eval_input)
    return result

@router.get("/{evaluation_id}", response_model=EvaluationResultResponse)
def get_evaluation_result(
    evaluation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    res = db.query(EvaluationResult).filter(EvaluationResult.id == evaluation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")
    return res

@router.put("/{evaluation_id}/review", response_model=EvaluationResultResponse)
def review_evaluation_result(
    evaluation_id: int,
    review_in: HumanReviewUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Support human review and override of LLM-as-a-judge scores.
    """
    res = db.query(EvaluationResult).filter(EvaluationResult.id == evaluation_id).first()
    if not res:
        raise HTTPException(status_code=404, detail="Evaluation record not found.")

    res.is_human_reviewed = True
    res.human_override_score = review_in.override_score
    res.score = review_in.override_score  # Update active score with human verified ground truth
    res.passed = review_in.passed
    res.human_notes = review_in.notes
    db.commit()
    db.refresh(res)
    return res
