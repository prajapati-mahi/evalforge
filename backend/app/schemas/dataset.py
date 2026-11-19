from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

class DatasetCaseBase(BaseModel):
    input_text: str
    expected_output: Optional[str] = None
    context: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None

class DatasetCaseCreate(DatasetCaseBase):
    pass

class DatasetCaseResponse(DatasetCaseBase):
    id: int
    dataset_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DatasetBase(BaseModel):
    name: str
    description: Optional[str] = None
    file_format: Optional[str] = "jsonl"

class DatasetCreate(DatasetBase):
    project_id: int
    initial_cases: Optional[List[DatasetCaseCreate]] = None

class DatasetUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class DatasetResponse(DatasetBase):
    id: int
    project_id: int
    version: int
    num_cases: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DatasetValidationError(BaseModel):
    row_index: int
    field: str
    error: str
    raw_data: Optional[Dict[str, Any]] = None

class DatasetValidationResult(BaseModel):
    is_valid: bool
    total_rows: int
    valid_rows: int
    invalid_rows: int
    errors: List[DatasetValidationError] = []
    warnings: List[str] = []
    preview: List[Dict[str, Any]] = []
