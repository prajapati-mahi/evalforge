from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.experiment import Experiment, ExperimentRun, TestCaseRun
from app.models.evaluation import EvaluationResult
from app.models.project import Project
from app.models.user import User
from app.schemas.dashboard import (
    DashboardMetricsResponse, MetricTimePoint, LatencyBucket, ModelBenchmarkItem
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics", response_model=DashboardMetricsResponse)
def get_dashboard_metrics(
    project_id: Optional[int] = None,
    time_range: str = Query("30d", pattern="^(24h|7d|30d|all)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Determine date threshold
    now = datetime.now(timezone.utc)
    cutoff = None
    if time_range == "24h":
        cutoff = now - timedelta(hours=24)
    elif time_range == "7d":
        cutoff = now - timedelta(days=7)
    elif time_range == "30d":
        cutoff = now - timedelta(days=30)

    # Base query for user's experiments
    user_project_ids = [
        p.id for p in db.query(Project.id).filter(Project.owner_id == current_user.id).all()
    ]
    if project_id:
        if project_id not in user_project_ids:
            user_project_ids = []
        else:
            user_project_ids = [project_id]

    if not user_project_ids:
        return DashboardMetricsResponse(
            total_evaluations=0,
            total_test_cases=0,
            avg_correctness=0.0,
            avg_faithfulness=0.0,
            avg_latency_ms=0.0,
            total_tokens=0,
            total_cost=0.0,
            failed_executions=0,
            success_rate=100.0,
            score_over_time=[],
            model_performance=[],
            latency_distribution=[],
            token_consumption_over_time=[],
            cost_over_time=[],
            success_vs_failure={"success": 0, "failed": 0},
            is_empty=True
        )

    exp_query = db.query(Experiment).filter(Experiment.project_id.in_(user_project_ids))
    if cutoff:
        exp_query = exp_query.filter(Experiment.created_at >= cutoff)
    experiments = exp_query.all()
    exp_ids = [e.id for e in experiments]

    if not exp_ids:
        return DashboardMetricsResponse(
            total_evaluations=0,
            total_test_cases=0,
            avg_correctness=0.0,
            avg_faithfulness=0.0,
            avg_latency_ms=0.0,
            total_tokens=0,
            total_cost=0.0,
            failed_executions=0,
            success_rate=100.0,
            score_over_time=[],
            model_performance=[],
            latency_distribution=[],
            token_consumption_over_time=[],
            cost_over_time=[],
            success_vs_failure={"success": 0, "failed": 0},
            is_empty=True
        )

    # Aggregate runs
    runs = db.query(ExperimentRun).filter(ExperimentRun.experiment_id.in_(exp_ids)).all()
    run_ids = [r.id for r in runs]

    case_runs = db.query(TestCaseRun).filter(TestCaseRun.experiment_run_id.in_(run_ids)).all() if run_ids else []

    total_evals = len(runs)
    total_cases = len(case_runs)

    succ_count = sum(1 for c in case_runs if c.status == "success")
    fail_count = sum(1 for c in case_runs if c.status != "success")
    success_rate = round((succ_count / total_cases * 100.0), 1) if total_cases > 0 else 100.0

    total_tokens = sum(c.total_tokens for c in case_runs)
    total_cost = round(sum(c.cost_estimate for c in case_runs), 4)
    avg_latency = round(sum(c.latency_ms for c in case_runs) / total_cases, 1) if total_cases > 0 else 0.0

    # Evaluator metrics
    correctness_scores = []
    faithfulness_scores = []

    case_ids = [c.id for c in case_runs]
    eval_results = db.query(EvaluationResult).filter(EvaluationResult.test_case_run_id.in_(case_ids)).all() if case_ids else []

    for ev in eval_results:
        if ev.metric_name == "correctness":
            correctness_scores.append(ev.score)
        elif ev.metric_name == "faithfulness":
            faithfulness_scores.append(ev.score)

    avg_correctness = round(sum(correctness_scores) / len(correctness_scores), 4) if correctness_scores else 0.0
    avg_faithfulness = round(sum(faithfulness_scores) / len(faithfulness_scores), 4) if faithfulness_scores else 0.0

    # 1. Score Over Time & Cost Over Time
    time_points = []
    token_time_points = []
    cost_time_points = []

    sorted_experiments = sorted(experiments, key=lambda x: x.created_at)
    for exp in sorted_experiments:
        date_str = exp.created_at.strftime("%b %d") if exp.created_at else "N/A"
        
        # calculate for this experiment
        exp_runs = [r for r in runs if r.experiment_id == exp.id]
        if not exp_runs:
            continue
        
        exp_run_ids = [r.id for r in exp_runs]
        exp_crs = [c for c in case_runs if c.experiment_run_id in exp_run_ids]
        
        c_score = 0.0
        f_score = 0.0
        exp_toks = sum(c.total_tokens for c in exp_crs)
        exp_cst = sum(c.cost_estimate for c in exp_crs)
        exp_lat = (sum(c.latency_ms for c in exp_crs) / len(exp_crs)) if exp_crs else 0.0

        # fetch evals
        sub_c_ids = [c.id for c in exp_crs]
        sub_evals = [e for e in eval_results if e.test_case_run_id in sub_c_ids]
        c_list = [e.score for e in sub_evals if e.metric_name == "correctness"]
        f_list = [e.score for e in sub_evals if e.metric_name == "faithfulness"]

        c_score = round(sum(c_list) / len(c_list) * 100.0, 1) if c_list else 0.0
        f_score = round(sum(f_list) / len(f_list) * 100.0, 1) if f_list else 0.0

        time_points.append(MetricTimePoint(
            timestamp=str(exp.created_at),
            date_label=date_str,
            correctness=c_score,
            faithfulness=f_score,
            cost=round(exp_cst, 4),
            latency=round(exp_lat, 1),
            tokens=exp_toks
        ))

        token_time_points.append({"date": date_str, "tokens": exp_toks, "experiment": exp.name})
        cost_time_points.append({"date": date_str, "cost": round(exp_cst, 4), "experiment": exp.name})

    # 2. Model Performance Breakdown
    model_benchmarks: Dict[str, Dict[str, Any]] = {}
    for r in runs:
        m = r.summary_metrics or {}
        if r.model_name not in model_benchmarks:
            model_benchmarks[r.model_name] = {
                "correctness": [],
                "faithfulness": [],
                "latencies": [],
                "costs": [],
                "count": 0
            }
        model_benchmarks[r.model_name]["correctness"].append(m.get("avg_correctness", 0.0))
        model_benchmarks[r.model_name]["faithfulness"].append(m.get("avg_faithfulness", 0.0))
        model_benchmarks[r.model_name]["latencies"].append(m.get("avg_latency_ms", 0.0))
        model_benchmarks[r.model_name]["costs"].append(m.get("total_cost", 0.0))
        model_benchmarks[r.model_name]["count"] += 1

    model_perf_list = []
    for model_name, data in model_benchmarks.items():
        cnt = max(1, data["count"])
        model_perf_list.append(ModelBenchmarkItem(
            model_name=model_name,
            correctness=round(sum(data["correctness"]) / cnt * 100.0, 1),
            faithfulness=round(sum(data["faithfulness"]) / cnt * 100.0, 1),
            latency_ms=round(sum(data["latencies"]) / cnt, 1),
            cost=round(sum(data["costs"]), 4),
            total_evals=cnt
        ))

    # 3. Latency Distribution
    buckets = [
        ("< 100ms", 0),
        ("100-300ms", 0),
        ("300-600ms", 0),
        ("600ms-1s", 0),
        ("> 1s", 0)
    ]
    b_counts = [0, 0, 0, 0, 0]
    for c in case_runs:
        lat = c.latency_ms
        if lat < 100:
            b_counts[0] += 1
        elif lat < 300:
            b_counts[1] += 1
        elif lat < 600:
            b_counts[2] += 1
        elif lat < 1000:
            b_counts[3] += 1
        else:
            b_counts[4] += 1

    latency_dist = [
        LatencyBucket(range_label=buckets[i][0], count=b_counts[i])
        for i in range(5)
    ]

    return DashboardMetricsResponse(
        total_evaluations=total_evals,
        total_test_cases=total_cases,
        avg_correctness=avg_correctness,
        avg_faithfulness=avg_faithfulness,
        avg_latency_ms=avg_latency,
        total_tokens=total_tokens,
        total_cost=total_cost,
        failed_executions=fail_count,
        success_rate=success_rate,
        score_over_time=time_points,
        model_performance=model_perf_list,
        latency_distribution=latency_dist,
        token_consumption_over_time=token_time_points,
        cost_over_time=cost_time_points,
        success_vs_failure={"success": succ_count, "failed": fail_count},
        is_empty=False
    )
