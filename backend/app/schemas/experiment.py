from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from app.schemas.evaluation import EvaluationResultResponse

class ExperimentConfig(BaseModel):
    models: List[str]  # e.g. ["mock-gpt-4o", "mock-claude-3-5-sonnet"]
    evaluators: List[str] = [
        "correctness",
        "faithfulness",
        "context_precision",
        "context_recall",
        "response_relevance",
        "hallucination"
    ]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024
    concurrency: Optional[int] = 3
    system_instruction: Optional[str] = None
    custom_evaluator_prompt: Optional[str] = None

class ExperimentCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    dataset_id: int
    prompt_version_id: Optional[int] = None
    config: ExperimentConfig

class TestCaseRunResponse(BaseModel):
    id: int
    experiment_run_id: int
    dataset_case_id: Optional[int] = None
    input_text: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    generated_output: Optional[str] = None
    status: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_estimate: float
    error_message: Optional[str] = None
    retry_count: int
    evaluations: List[EvaluationResultResponse] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ExperimentRunResponse(BaseModel):
    id: int
    experiment_id: int
    model_name: str
    provider_name: str
    status: str
    summary_metrics: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    test_case_runs: Optional[List[TestCaseRunResponse]] = None

    model_config = ConfigDict(from_attributes=True)

class ExperimentResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    status: str
    dataset_id: Optional[int] = None
    prompt_version_id: Optional[int] = None
    config_json: Optional[Dict[str, Any]] = None
    total_cases: int
    processed_cases: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    runs: List[ExperimentRunResponse] = []

    model_config = ConfigDict(from_attributes=True)
