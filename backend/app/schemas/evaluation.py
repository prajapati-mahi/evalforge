from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field

class EvaluationResultResponse(BaseModel):
    id: int
    test_case_run_id: int
    metric_name: str
    score: float
    passed: bool
    reasoning: Optional[str] = None
    supported_claims: Optional[List[str]] = []
    unsupported_claims: Optional[List[str]] = []
    evidence: Optional[str] = None
    latency_ms: float
    is_human_reviewed: bool
    human_override_score: Optional[float] = None
    human_notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class HumanReviewUpdate(BaseModel):
    override_score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    notes: Optional[str] = None

class SingleEvalRequest(BaseModel):
    metric_name: str
    query: str
    response: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    judge_model: Optional[str] = "mock-gpt-4o"

class JudgeEvaluationOutput(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    reasoning: str
    supported_claims: List[str] = []
    unsupported_claims: List[str] = []
    evidence: Optional[str] = None
