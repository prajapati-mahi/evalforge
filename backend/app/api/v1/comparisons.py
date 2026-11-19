from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.experiment import Experiment, ExperimentRun, TestCaseRun
from app.models.dataset import Dataset, DatasetCase
from app.models.user import User
from app.schemas.comparison import (
    ModelComparisonRequest, ModelComparisonResponse, ModelStatSummary
)
from app.api.deps import get_current_user, verify_project_access

router = APIRouter(prefix="/comparisons", tags=["Comparisons"])

@router.post("", response_model=ModelComparisonResponse)
def compare_models(
    req: ModelComparisonRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == req.experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)

    dataset = db.query(Dataset).filter(Dataset.id == exp.dataset_id).first()
    dataset_name = dataset.name if dataset else "Default Dataset"

    runs = db.query(ExperimentRun).filter(ExperimentRun.experiment_id == exp.id).all()
    if req.model_names:
        runs = [r for r in runs if r.model_name in req.model_names]

    if not runs:
        raise HTTPException(status_code=400, detail="No matching model runs found for this experiment.")

    model_names = [r.model_name for r in runs]
    
    # 1. Build Model Summaries
    summaries: List[ModelStatSummary] = []
    for r in runs:
        m = r.summary_metrics or {}
        succ = m.get("success_count", 0)
        fail = m.get("fail_count", 0)
        tot = succ + fail
        rate = round((succ / tot * 100.0), 1) if tot > 0 else 100.0

        summaries.append(ModelStatSummary(
            model_name=r.model_name,
            provider_name=r.provider_name,
            avg_correctness=m.get("avg_correctness", 0.0),
            avg_faithfulness=m.get("avg_faithfulness", 0.0),
            avg_context_precision=m.get("avg_context_precision", 0.0),
            avg_context_recall=m.get("avg_context_recall", 0.0),
            avg_relevance=m.get("avg_relevance", 0.0),
            avg_hallucination_score=m.get("avg_hallucination_score", 0.0),
            avg_latency_ms=m.get("avg_latency_ms", 0.0),
            total_tokens=m.get("total_tokens", 0),
            total_cost=m.get("total_cost", 0.0),
            success_rate=rate,
            total_runs=tot,
            win_rate=0.0
        ))

    # Calculate win rate based on top correctness per test case
    case_winners: Dict[str, int] = {m: 0 for m in model_names}
    cases = db.query(DatasetCase).filter(DatasetCase.dataset_id == exp.dataset_id).all()
    
    side_by_side = []
    for c in cases:
        case_item = {
            "case_id": c.id,
            "input": c.input_text,
            "expected": c.expected_output,
            "models": {}
        }
        best_case_score = -1.0
        best_case_model = None

        for r in runs:
            cr = (
                db.query(TestCaseRun)
                .filter(TestCaseRun.experiment_run_id == r.id, TestCaseRun.dataset_case_id == c.id)
                .first()
            )
            if cr:
                # get correctness score
                score = 0.0
                for ev in cr.evaluations:
                    if ev.metric_name == "correctness":
                        score = ev.score
                        break
                case_item["models"][r.model_name] = {
                    "output": cr.generated_output,
                    "latency_ms": cr.latency_ms,
                    "tokens": cr.total_tokens,
                    "cost": cr.cost_estimate,
                    "correctness": score,
                    "status": cr.status
                }
                if score > best_case_score:
                    best_case_score = score
                    best_case_model = r.model_name

        if best_case_model:
            case_winners[best_case_model] += 1
        side_by_side.append(case_item)

    total_evaluated_cases = max(1, len(cases))
    for s in summaries:
        s.win_rate = round((case_winners.get(s.model_name, 0) / total_evaluated_cases) * 100.0, 1)

    # 2. Build Radar Chart Format
    # Dimensions: Correctness, Faithfulness, Relevance, Precision, Recall, Grounding
    metrics_dimensions = [
        ("Correctness", "avg_correctness"),
        ("Faithfulness", "avg_faithfulness"),
        ("Context Precision", "avg_context_precision"),
        ("Context Recall", "avg_context_recall"),
        ("Relevance", "avg_relevance"),
        ("Grounding", "avg_hallucination_score")
    ]
    radar_data = []
    for dim_label, metric_key in metrics_dimensions:
        item: Dict[str, Any] = {"metric": dim_label}
        for s in summaries:
            val = getattr(s, metric_key, 0.0)
            item[s.model_name] = round(val * 100.0, 1)  # 0 to 100 scale for radar
        radar_data.append(item)

    return ModelComparisonResponse(
        experiment_id=exp.id,
        experiment_name=exp.name,
        dataset_name=dataset_name,
        models=model_names,
        radar_data=radar_data,
        model_summaries=summaries,
        side_by_side_cases=side_by_side
    )
