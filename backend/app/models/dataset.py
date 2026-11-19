from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(Integer, default=1)
    num_cases = Column(Integer, default=0)
    file_format = Column(String(50), default="jsonl")  # jsonl, csv, manual
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="datasets")
    cases = relationship("DatasetCase", back_populates="dataset", cascade="all, delete-orphan")
    experiments = relationship("Experiment", back_populates="dataset")

class DatasetCase(Base):
    __tablename__ = "dataset_cases"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    input_text = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # retrieved context or ground truth context
    metadata_json = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    dataset = relationship("Dataset", back_populates="cases")
    test_runs = relationship("TestCaseRun", back_populates="dataset_case")
