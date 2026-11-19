from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from app.core.database import Base

class BackgroundJob(Base):
    __tablename__ = "background_jobs"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, index=True, nullable=False)
    job_type = Column(String(50), nullable=False)  # experiment_run, dataset_validation, report_generation
    status = Column(String(50), default="pending")  # pending, queued, running, completed, failed, cancelled
    progress = Column(Float, default=0.0)  # 0.0 to 100.0
    payload_json = Column(JSON, nullable=True, default=dict)
    result_json = Column(JSON, nullable=True, default=dict)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
