from typing import Optional, List
from pydantic import BaseModel

class ReportGenerateRequest(BaseModel):
    experiment_id: int
    format: str = "pdf"  # pdf or csv
    include_traces: bool = True
    include_full_cases: bool = True

class ReportResponse(BaseModel):
    report_id: str
    experiment_id: int
    filename: str
    download_url: str
    generated_at: str
    file_size_bytes: int
