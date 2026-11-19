from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.models.trace import Trace, TraceSpan
from app.tracing.redactor import redact_secrets

class ExecutionTracer:
    """
    Manages end-to-end tracing and hierarchical span creation for LLM executions.
    """
    def __init__(
        self,
        db: Session,
        project_id: int,
        trace_name: str,
        experiment_id: Optional[int] = None,
        test_case_run_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.db = db
        self.trace = Trace(
            project_id=project_id,
            experiment_id=experiment_id,
            test_case_run_id=test_case_run_id,
            trace_name=trace_name,
            status="running",
            start_time=datetime.now(timezone.utc),
            metadata_json=metadata or {}
        )
        self.db.add(self.trace)
        self.db.commit()
        self.db.refresh(self.trace)
        self.spans: List[TraceSpan] = []

    def start_span(
        self,
        span_name: str,
        span_type: str,
        input_data: Optional[str] = None,
        parent_span_id: Optional[int] = None,
        attributes: Optional[Dict[str, Any]] = None
    ) -> TraceSpan:
        span = TraceSpan(
            trace_id=self.trace.id,
            parent_span_id=parent_span_id,
            span_name=span_name,
            span_type=span_type,
            start_time=datetime.now(timezone.utc),
            input_data=redact_secrets(input_data) if input_data else None,
            attributes_json=attributes or {},
            status="running"
        )
        self.db.add(span)
        self.db.commit()
        self.db.refresh(span)
        self.spans.append(span)
        return span

    def end_span(
        self,
        span: TraceSpan,
        output_data: Optional[str] = None,
        status: str = "success",
        error_message: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None
    ):
        span.end_time = datetime.now(timezone.utc)
        start_ts = span.start_time.replace(tzinfo=timezone.utc).timestamp() if span.start_time.tzinfo is None else span.start_time.timestamp()
        end_ts = span.end_time.timestamp()
        span.latency_ms = round((end_ts - start_ts) * 1000.0, 2)
        span.output_data = redact_secrets(output_data) if output_data else None
        span.status = status
        span.error_message = redact_secrets(error_message) if error_message else None
        if attributes:
            current_attrs = span.attributes_json or {}
            current_attrs.update(attributes)
            span.attributes_json = current_attrs
        self.db.commit()

    def complete_trace(
        self,
        status: str = "success",
        total_tokens: int = 0,
        total_cost: float = 0.0,
        metadata_update: Optional[Dict[str, Any]] = None
    ):
        self.trace.end_time = datetime.now(timezone.utc)
        start_ts = self.trace.start_time.replace(tzinfo=timezone.utc).timestamp() if self.trace.start_time.tzinfo is None else self.trace.start_time.timestamp()
        end_ts = self.trace.end_time.timestamp()
        self.trace.latency_ms = round((end_ts - start_ts) * 1000.0, 2)
        self.trace.status = status
        self.trace.total_tokens = total_tokens
        self.trace.total_cost = total_cost
        if metadata_update:
            meta = self.trace.metadata_json or {}
            meta.update(metadata_update)
            self.trace.metadata_json = meta
        self.db.commit()
        self.db.refresh(self.trace)
        return self.trace
