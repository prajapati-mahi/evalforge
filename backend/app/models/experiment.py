from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float
from sqlalchemy.orm import relationship
from app.core.database import Base

class Experiment(Base):
    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # pending, queued, running, completed, failed, cancelled
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="SET NULL"), nullable=True)
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id", ondelete="SET NULL"), nullable=True)
    config_json = Column(JSON, nullable=True, default=dict)  # models list, params, evaluators
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_cases = Column(Integer, default=0)
    processed_cases = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="experiments")
    dataset = relationship("Dataset", back_populates="experiments")
    prompt_version = relationship("PromptVersion", back_populates="experiments")
    runs = relationship("ExperimentRun", back_populates="experiment", cascade="all, delete-orphan")
    traces = relationship("Trace", back_populates="experiment", cascade="all, delete-orphan")

class ExperimentRun(Base):
    __tablename__ = "experiment_runs"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False)
    model_name = Column(String(100), nullable=False)
    provider_name = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    
    # Pre-aggregated summary metrics for rapid comparisons and dashboards
    summary_metrics = Column(JSON, nullable=True, default=dict)
    # {
    #   "avg_correctness": 0.85,
    #   "avg_faithfulness": 0.90,
    #   "avg_context_precision": 0.82,
    #   "avg_context_recall": 0.88,
    #   "avg_relevance": 0.91,
    #   "avg_hallucination_score": 0.08,
    #   "avg_latency_ms": 420.5,
    #   "total_tokens": 12400,
    #   "total_cost": 0.0345,
    #   "success_count": 20,
    #   "fail_count": 0
    # }
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    experiment = relationship("Experiment", back_populates="runs")
    test_case_runs = relationship("TestCaseRun", back_populates="experiment_run", cascade="all, delete-orphan")

class TestCaseRun(Base):
    __tablename__ = "test_case_runs"

    id = Column(Integer, primary_key=True, index=True)
    experiment_run_id = Column(Integer, ForeignKey("experiment_runs.id", ondelete="CASCADE"), nullable=False)
    dataset_case_id = Column(Integer, ForeignKey("dataset_cases.id", ondelete="SET NULL"), nullable=True)
    input_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    context = Column(Text, nullable=True)
    generated_output = Column(Text, nullable=True)
    status = Column(String(50), default="pending")  # success, error, pending
    latency_ms = Column(Float, default=0.0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    cost_estimate = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    experiment_run = relationship("ExperimentRun", back_populates="test_case_runs")
    dataset_case = relationship("DatasetCase", back_populates="test_runs")
    evaluations = relationship("EvaluationResult", back_populates="test_case_run", cascade="all, delete-orphan")
    traces = relationship("Trace", back_populates="test_case_run")
