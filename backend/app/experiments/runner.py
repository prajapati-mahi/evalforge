import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.experiment import Experiment, ExperimentRun, TestCaseRun
from app.models.dataset import Dataset, DatasetCase
from app.models.prompt import PromptVersion
from app.models.evaluation import EvaluationResult
from app.models.job import BackgroundJob
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest
from app.evaluators.base import EvaluatorInput
from app.evaluators.registry import run_evaluators
from app.core.pricing import estimate_cost
from app.tracing.tracer import ExecutionTracer

async def execute_experiment_pipeline(
    db: Session,
    experiment_id: int,
    background_job_id: Optional[str] = None
):
    """
    Main asynchronous pipeline for executing an evaluation experiment.
    Runs each model against all test cases, records traces and spans,
    and computes full evaluation metrics.
    """
    experiment: Optional[Experiment] = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not experiment:
        return

    # Update experiment status
    experiment.status = "running"
    experiment.started_at = datetime.now(timezone.utc)
    db.commit()

    if background_job_id:
        job = db.query(BackgroundJob).filter(BackgroundJob.task_id == background_job_id).first()
        if job:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            db.commit()

    try:
        # Load dataset cases
        dataset_cases: List[DatasetCase] = (
            db.query(DatasetCase)
            .filter(DatasetCase.dataset_id == experiment.dataset_id)
            .all()
        )
        if not dataset_cases:
            experiment.status = "failed"
            experiment.error_message = "Dataset has 0 test cases."
            experiment.completed_at = datetime.now(timezone.utc)
            db.commit()
            return

        # Load prompt version if specified
        prompt_version: Optional[PromptVersion] = None
        if experiment.prompt_version_id:
            prompt_version = db.query(PromptVersion).filter(PromptVersion.id == experiment.prompt_version_id).first()

        config = experiment.config_json or {}
        models_to_test: List[str] = config.get("models", ["mock-gpt-4o"])
        evaluator_names: List[str] = config.get("evaluators", ["correctness", "faithfulness", "relevance"])
        temperature: float = config.get("temperature", 0.7)
        max_tokens: int = config.get("max_tokens", 1024)
        judge_model: str = config.get("judge_model", "mock-gpt-4o")

        total_work = len(models_to_test) * len(dataset_cases)
        experiment.total_cases = total_work
        experiment.processed_cases = 0
        db.commit()

        # Iterate through each model
        for model_name in models_to_test:
            # Check for cancellation
            db.refresh(experiment)
            if experiment.status == "cancelled":
                break

            provider_name = infer_provider_from_model(model_name)
            adapter = get_provider_adapter(provider_name)

            exp_run = ExperimentRun(
                experiment_id=experiment.id,
                model_name=model_name,
                provider_name=provider_name,
                status="running",
                started_at=datetime.now(timezone.utc)
            )
            db.add(exp_run)
            db.commit()
            db.refresh(exp_run)

            run_correctness_scores = []
            run_faithfulness_scores = []
            run_prec_scores = []
            run_recall_scores = []
            run_rel_scores = []
            run_hallucination_scores = []
            run_latencies = []
            total_tokens_run = 0
            total_cost_run = 0.0
            success_count = 0
            fail_count = 0

            for case in dataset_cases:
                # Check for cancellation mid-run
                db.refresh(experiment)
                if experiment.status == "cancelled":
                    exp_run.status = "cancelled"
                    break

                # Prepare prompt text
                if prompt_version:
                    prompt_text = prompt_version.template_text.replace("{{input}}", case.input_text)
                    if case.context:
                        prompt_text = prompt_text.replace("{{context}}", case.context)
                    sys_instruction = prompt_version.system_instruction
                else:
                    prompt_text = case.input_text
                    sys_instruction = config.get("system_instruction")

                # Setup tracer
                tracer = ExecutionTracer(
                    db=db,
                    project_id=experiment.project_id,
                    trace_name=f"eval_{model_name}_{case.id}",
                    experiment_id=experiment.id,
                    metadata={"case_id": case.id, "model": model_name}
                )

                # Retrieval Span (if context exists)
                if case.context:
                    retrieval_span = tracer.start_span(
                        span_name="Context Retrieval",
                        span_type="retrieval",
                        input_data=case.input_text,
                        attributes={"context_length": len(case.context)}
                    )
                    tracer.end_span(retrieval_span, output_data=case.context[:200])

                # Model Generation Span
                model_span = tracer.start_span(
                    span_name=f"Generation: {model_name}",
                    span_type="model_generation",
                    input_data=prompt_text,
                    attributes={"model": model_name, "temperature": temperature}
                )

                req = LLMRequest(
                    prompt=prompt_text,
                    system_instruction=sys_instruction,
                    model_name=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )

                response = await adapter.generate(req)
                
                cost = estimate_cost(
                    model_name=model_name,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens
                )

                status_case = "error" if response.error else "success"
                if status_case == "success":
                    success_count += 1
                else:
                    fail_count += 1

                tracer.end_span(
                    model_span,
                    output_data=response.text or response.error,
                    status=status_case,
                    error_message=response.error,
                    attributes={"input_tokens": response.input_tokens, "output_tokens": response.output_tokens, "cost": cost}
                )

                # Save TestCaseRun
                tc_run = TestCaseRun(
                    experiment_run_id=exp_run.id,
                    dataset_case_id=case.id,
                    input_text=case.input_text,
                    expected_output=case.expected_output,
                    context=case.context,
                    generated_output=response.text or "",
                    status=status_case,
                    latency_ms=response.latency_ms,
                    input_tokens=response.input_tokens,
                    output_tokens=response.output_tokens,
                    total_tokens=response.total_tokens,
                    cost_estimate=cost,
                    error_message=response.error
                )
                db.add(tc_run)
                db.commit()
                db.refresh(tc_run)

                tracer.trace.test_case_run_id = tc_run.id
                db.commit()

                # Evaluation Span
                if status_case == "success":
                    eval_span = tracer.start_span(
                        span_name="Evaluation Engine",
                        span_type="evaluation",
                        attributes={"evaluators": evaluator_names}
                    )

                    eval_input = EvaluatorInput(
                        query=case.input_text,
                        response=response.text,
                        expected_output=case.expected_output,
                        context=case.context,
                        judge_model=judge_model
                    )

                    eval_results = await run_evaluators(evaluator_names, eval_input)
                    
                    for ev in eval_results:
                        er_record = EvaluationResult(
                            test_case_run_id=tc_run.id,
                            metric_name=ev.metric_name,
                            score=ev.score,
                            passed=ev.passed,
                            reasoning=ev.reasoning,
                            supported_claims=ev.supported_claims,
                            unsupported_claims=ev.unsupported_claims,
                            evidence=ev.evidence,
                            latency_ms=ev.latency_ms
                        )
                        db.add(er_record)
                        
                        # Accumulate metrics
                        if ev.metric_name == "correctness":
                            run_correctness_scores.append(ev.score)
                        elif ev.metric_name == "faithfulness":
                            run_faithfulness_scores.append(ev.score)
                        elif ev.metric_name == "context_precision":
                            run_prec_scores.append(ev.score)
                        elif ev.metric_name == "context_recall":
                            run_recall_scores.append(ev.score)
                        elif ev.metric_name in ("relevance", "response_relevance"):
                            run_rel_scores.append(ev.score)
                        elif ev.metric_name == "hallucination":
                            run_hallucination_scores.append(ev.score)

                    db.commit()
                    tracer.end_span(eval_span, output_data=f"Evaluated {len(eval_results)} metrics")

                # Complete trace
                tracer.complete_trace(
                    status=status_case,
                    total_tokens=response.total_tokens,
                    total_cost=cost
                )

                total_tokens_run += response.total_tokens
                total_cost_run += cost
                run_latencies.append(response.latency_ms)

                # Update progress
                experiment.processed_cases += 1
                if background_job_id and job:
                    job.progress = round((experiment.processed_cases / total_work) * 100.0, 1)
                db.commit()

            # Finish ExperimentRun summary metrics
            avg = lambda l: round(sum(l) / len(l), 4) if l else 0.0
            exp_run.summary_metrics = {
                "avg_correctness": avg(run_correctness_scores),
                "avg_faithfulness": avg(run_faithfulness_scores),
                "avg_context_precision": avg(run_prec_scores),
                "avg_context_recall": avg(run_recall_scores),
                "avg_relevance": avg(run_rel_scores),
                "avg_hallucination_score": avg(run_hallucination_scores),
                "avg_latency_ms": round(avg(run_latencies), 2),
                "total_tokens": total_tokens_run,
                "total_cost": round(total_cost_run, 6),
                "success_count": success_count,
                "fail_count": fail_count
            }
            exp_run.status = "completed" if exp_run.status != "cancelled" else "cancelled"
            exp_run.completed_at = datetime.now(timezone.utc)
            db.commit()

        if experiment.status != "cancelled":
            experiment.status = "completed"
        experiment.completed_at = datetime.now(timezone.utc)
        
        if background_job_id and job:
            job.status = experiment.status
            job.progress = 100.0
            job.completed_at = datetime.now(timezone.utc)
        db.commit()

    except Exception as e:
        experiment.status = "failed"
        experiment.error_message = str(e)
        experiment.completed_at = datetime.now(timezone.utc)
        if background_job_id and job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.now(timezone.utc)
        db.commit()
