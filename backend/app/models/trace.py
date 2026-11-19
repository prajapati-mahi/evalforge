from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Trace(Base):
    __tablename__ = "traces"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True)
    test_case_run_id = Column(Integer, ForeignKey("test_case_runs.id", ondelete="SET NULL"), nullable=True)
    trace_name = Column(String(255), nullable=False)
    status = Column(String(50), default="success")  # success, error
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    latency_ms = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="traces")
    experiment = relationship("Experiment", back_populates="traces")
    test_case_run = relationship("TestCaseRun", back_populates="traces")
    spans = relationship("TraceSpan", back_populates="trace", cascade="all, delete-orphan", order_by="TraceSpan.start_time.asc()")

class TraceSpan(Base):
    __tablename__ = "trace_spans"

    id = Column(Integer, primary_key=True, index=True)
    trace_id = Column(Integer, ForeignKey("traces.id", ondelete="CASCADE"), nullable=False)
    parent_span_id = Column(Integer, ForeignKey("trace_spans.id", ondelete="SET NULL"), nullable=True)
    span_name = Column(String(255), nullable=False)
    span_type = Column(String(50), nullable=False)  # retrieval, model_generation, tool_execution, evaluation
    start_time = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    end_time = Column(DateTime, nullable=True)
    latency_ms = Column(Float, default=0.0)
    input_data = Column(Text, nullable=True)  # sanitized & redacted input
    output_data = Column(Text, nullable=True)  # sanitized & redacted output
    status = Column(String(50), default="success")  # success, error
    error_message = Column(Text, nullable=True)
    attributes_json = Column(JSON, nullable=True, default=dict)  # token count, model, temperature, tool args
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    trace = relationship("Trace", back_populates="spans")
    children = relationship("TraceSpan", backref="parent", remote_side=[id])
