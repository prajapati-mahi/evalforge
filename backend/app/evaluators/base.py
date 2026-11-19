from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class EvaluatorInput(BaseModel):
    query: str
    response: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    judge_model: str = "mock-gpt-4o"
    judge_api_key: Optional[str] = None

class EvaluatorOutput(BaseModel):
    metric_name: str
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    reasoning: str
    supported_claims: List[str] = []
    unsupported_claims: List[str] = []
    evidence: Optional[str] = None
    latency_ms: float = 0.0
    error: Optional[str] = None

class BaseEvaluator(ABC):
    name: str = "base_evaluator"
    description: str = "Base interface for all EvalForge metrics"

    @abstractmethod
    async def evaluate(self, input_data: EvaluatorInput) -> EvaluatorOutput:
        """Run evaluation calculation and return structured output."""
        pass
