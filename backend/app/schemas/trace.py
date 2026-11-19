from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class TraceSpanResponse(BaseModel):
    id: int
    trace_id: int
    parent_span_id: Optional[int] = None
    span_name: str
    span_type: str  # retrieval, model_generation, tool_execution, evaluation
    start_time: datetime
    end_time: Optional[datetime] = None
    latency_ms: float
    input_data: Optional[str] = None
    output_data: Optional[str] = None
    status: str
    error_message: Optional[str] = None
    attributes_json: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)

class TraceResponse(BaseModel):
    id: int
    project_id: int
    experiment_id: Optional[int] = None
    test_case_run_id: Optional[int] = None
    trace_name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    latency_ms: float
    total_tokens: int
    total_cost: float
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    spans: List[TraceSpanResponse] = []

    model_config = ConfigDict(from_attributes=True)

class TraceFilter(BaseModel):
    project_id: Optional[int] = None
    status: Optional[str] = None
    model_name: Optional[str] = None
    search: Optional[str] = None
    limit: int = 50
    offset: int = 0
