from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MetricComparisonItem(BaseModel):
    metric_name: str
    scores: Dict[str, float]  # model_name -> score

class ModelStatSummary(BaseModel):
    model_name: str
    provider_name: str
    avg_correctness: float
    avg_faithfulness: float
    avg_context_precision: float
    avg_context_recall: float
    avg_relevance: float
    avg_hallucination_score: float
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    success_rate: float
    total_runs: int
    win_rate: Optional[float] = None  # percentage of cases where this model achieved top overall score

class ModelComparisonRequest(BaseModel):
    experiment_id: int
    model_names: Optional[List[str]] = None

class ModelComparisonResponse(BaseModel):
    experiment_id: int
    experiment_name: str
    dataset_name: str
    models: List[str]
    radar_data: List[Dict[str, Any]]  # format: [{"metric": "Correctness", "Model A": 0.85, "Model B": 0.72}, ...]
    model_summaries: List[ModelStatSummary]
    side_by_side_cases: List[Dict[str, Any]]
