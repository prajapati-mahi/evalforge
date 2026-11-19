from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    project_type: str = "general"  # general, rag, qa, summarization, classification, agentic
    default_model: str = "mock-gpt-4o"

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = None
    default_model: Optional[str] = None

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    num_datasets: Optional[int] = 0
    num_experiments: Optional[int] = 0
    num_traces: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)
