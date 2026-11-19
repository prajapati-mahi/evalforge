from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class PromptVersionBase(BaseModel):
    template_text: str
    system_instruction: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None
    change_summary: Optional[str] = None

class PromptVersionCreate(PromptVersionBase):
    pass

class PromptVersionResponse(PromptVersionBase):
    id: int
    prompt_id: int
    version_number: int
    variables: List[str] = []
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PromptBase(BaseModel):
    name: str
    description: Optional[str] = None

class PromptCreate(PromptBase):
    project_id: int
    initial_template: str
    system_instruction: Optional[str] = None
    model_parameters: Optional[Dict[str, Any]] = None

class PromptUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PromptResponse(PromptBase):
    id: int
    project_id: int
    current_version: int
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[PromptVersionResponse] = None

    model_config = ConfigDict(from_attributes=True)

class PromptTestRequest(BaseModel):
    template_text: str
    system_instruction: Optional[str] = None
    variables: Dict[str, str] = {}
    model_name: str = "mock-gpt-4o"
    parameters: Optional[Dict[str, Any]] = None

class PromptTestResponse(BaseModel):
    rendered_prompt: str
    response_text: str
    model_name: str
    latency_ms: float
    input_tokens: int
    output_tokens: int
    cost_estimate: float
