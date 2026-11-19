from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MetricTimePoint(BaseModel):
    timestamp: str
    date_label: str
    correctness: float
    faithfulness: float
    cost: float
    latency: float
    tokens: int

class LatencyBucket(BaseModel):
    range_label: str
    count: int

class ModelBenchmarkItem(BaseModel):
    model_name: str
    correctness: float
    faithfulness: float
    latency_ms: float
    cost: float
    total_evals: int

class DashboardMetricsResponse(BaseModel):
    total_evaluations: int
    total_test_cases: int
    avg_correctness: float
    avg_faithfulness: float
    avg_latency_ms: float
    total_tokens: int
    total_cost: float
    failed_executions: int
    success_rate: float
    
    # Interactive chart series
    score_over_time: List[MetricTimePoint]
    model_performance: List[ModelBenchmarkItem]
    latency_distribution: List[LatencyBucket]
    token_consumption_over_time: List[Dict[str, Any]]
    cost_over_time: List[Dict[str, Any]]
    success_vs_failure: Dict[str, int]
    is_empty: bool = False
