from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base

class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    current_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="prompts")
    versions = relationship("PromptVersion", back_populates="prompt", cascade="all, delete-orphan", order_by="PromptVersion.version_number.desc()")

class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, index=True)
    prompt_id = Column(Integer, ForeignKey("prompts.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, nullable=False)
    template_text = Column(Text, nullable=False)
    system_instruction = Column(Text, nullable=True)
    variables = Column(JSON, nullable=True, default=list)  # list of extracted variable names like ["question", "context"]
    model_parameters = Column(JSON, nullable=True, default=dict)  # temperature, max_tokens, etc.
    change_summary = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    prompt = relationship("Prompt", back_populates="versions")
    experiments = relationship("Experiment", back_populates="prompt_version")
