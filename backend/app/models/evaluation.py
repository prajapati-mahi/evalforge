from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Float, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class EvaluationResult(Base):
    __tablename__ = "evaluation_results"

    id = Column(Integer, primary_key=True, index=True)
    test_case_run_id = Column(Integer, ForeignKey("test_case_runs.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(100), nullable=False)  # correctness, faithfulness, context_precision, context_recall, response_relevance, hallucination
    score = Column(Float, nullable=False)  # 0.0 to 1.0
    passed = Column(Boolean, default=True)
    reasoning = Column(Text, nullable=True)
    supported_claims = Column(JSON, nullable=True, default=list)
    unsupported_claims = Column(JSON, nullable=True, default=list)
    evidence = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0)
    
    # Human Review Support (Required by prompt: "Include an option for manual review of evaluation results")
    is_human_reviewed = Column(Boolean, default=False)
    human_override_score = Column(Float, nullable=True)
    human_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    test_case_run = relationship("TestCaseRun", back_populates="evaluations")
