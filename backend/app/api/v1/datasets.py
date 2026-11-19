import csv
import io
import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dataset import Dataset, DatasetCase
from app.models.user import User
from app.schemas.dataset import (
    DatasetCreate, DatasetUpdate, DatasetResponse,
    DatasetCaseCreate, DatasetCaseResponse,
    DatasetValidationResult, DatasetValidationError
)
from app.api.deps import get_current_user, verify_project_access

router = APIRouter(prefix="/datasets", tags=["Datasets"])

SAMPLE_BENCHMARK_CASES = [
    {
        "input_text": "What is the primary role of Retrieval-Augmented Generation (RAG)?",
        "expected_output": "RAG enhances LLM responses by fetching relevant factual context from external knowledge bases before generation.",
        "context": "Retrieval-Augmented Generation (RAG) is an AI framework that retrieves relevant documents from an external knowledge repository to ground model answers in factual sources.",
        "metadata_json": {"category": "architecture", "difficulty": "medium"}
    },
    {
        "input_text": "Which metric measures whether generated claims are supported by context?",
        "expected_output": "Faithfulness evaluates whether claims in the model output are supported by the provided context.",
        "context": "Faithfulness assesses the grounding of the generated answer by verifying if all claims can be inferred from the retrieved passages.",
        "metadata_json": {"category": "metrics", "difficulty": "easy"}
    },
    {
        "input_text": "What does context recall evaluate in a RAG pipeline?",
        "expected_output": "Context recall measures whether the retrieved context contains all the necessary information needed to answer the question.",
        "context": "Context recall measures the extent to which retrieved passages cover the ground-truth facts required to formulate the complete answer.",
        "metadata_json": {"category": "metrics", "difficulty": "medium"}
    },
    {
        "input_text": "Explain the difference between Hallucination and Low Context Precision.",
        "expected_output": "Hallucination refers to generating fabricated claims unsupported by truth/context, while low context precision means retrieving irrelevant noise alongside useful chunks.",
        "context": "Context precision measures the signal-to-noise ratio of retrieved chunks. Hallucination occurs when an LLM produces assertions that diverge from contextual reality.",
        "metadata_json": {"category": "reliability", "difficulty": "hard"}
    },
    {
        "input_text": "What is the formula for calculating total execution cost for an LLM call?",
        "expected_output": "Cost = (Input Tokens / 1M * Input Rate) + (Output Tokens / 1M * Output Rate).",
        "context": "Token pricing is quoted per 1,000,000 tokens for prompt ingestion and completion output separately.",
        "metadata_json": {"category": "economics", "difficulty": "easy"}
    }
]

@router.get("", response_model=List[DatasetResponse])
def list_datasets(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Dataset)
    if project_id:
        verify_project_access(project_id, user=current_user, db=db)
        query = query.filter(Dataset.project_id == project_id)
    else:
        # Filter to datasets under user's owned projects
        from app.models.project import Project
        user_proj_ids = [p.id for p in db.query(Project.id).filter(Project.owner_id == current_user.id).all()]
        query = query.filter(Dataset.project_id.in_(user_proj_ids))

    return query.order_by(Dataset.created_at.desc()).all()

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
def create_dataset(
    dataset_in: DatasetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_project_access(dataset_in.project_id, user=current_user, db=db)
    
    num_cases = len(dataset_in.initial_cases) if dataset_in.initial_cases else 0
    dataset = Dataset(
        project_id=dataset_in.project_id,
        name=dataset_in.name,
        description=dataset_in.description,
        file_format=dataset_in.file_format or "jsonl",
        num_cases=num_cases
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    if dataset_in.initial_cases:
        for c in dataset_in.initial_cases:
            case = DatasetCase(
                dataset_id=dataset.id,
                input_text=c.input_text,
                expected_output=c.expected_output,
                context=c.context,
                metadata_json=c.metadata_json or {}
            )
            db.add(case)
        db.commit()

    return dataset

@router.post("/seed-sample", response_model=DatasetResponse)
def seed_sample_dataset(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_project_access(project_id, user=current_user, db=db)

    dataset = Dataset(
        project_id=project_id,
        name="RAG & LLM Reliability Benchmark v1",
        description="Standard evaluation suite covering architecture, faithfulness, context recall, and hallucination scenarios.",
        file_format="jsonl",
        num_cases=len(SAMPLE_BENCHMARK_CASES)
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    for c in SAMPLE_BENCHMARK_CASES:
        case = DatasetCase(
            dataset_id=dataset.id,
            input_text=c["input_text"],
            expected_output=c["expected_output"],
            context=c["context"],
            metadata_json=c["metadata_json"]
        )
        db.add(case)
    db.commit()
    db.refresh(dataset)
    return dataset

@router.get("/{dataset_id}", response_model=DatasetResponse)
def get_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    verify_project_access(dataset.project_id, user=current_user, db=db)
    return dataset

@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    verify_project_access(dataset.project_id, user=current_user, db=db)
    db.delete(dataset)
    db.commit()
    return None

@router.get("/{dataset_id}/cases", response_model=List[DatasetCaseResponse])
def get_dataset_cases(
    dataset_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    verify_project_access(dataset.project_id, user=current_user, db=db)
    cases = db.query(DatasetCase).filter(DatasetCase.dataset_id == dataset.id).offset(skip).limit(limit).all()
    return cases

@router.post("/{dataset_id}/cases", response_model=DatasetCaseResponse, status_code=status.HTTP_201_CREATED)
def add_dataset_case(
    dataset_id: int,
    case_in: DatasetCaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    verify_project_access(dataset.project_id, user=current_user, db=db)

    case = DatasetCase(
        dataset_id=dataset.id,
        input_text=case_in.input_text,
        expected_output=case_in.expected_output,
        context=case_in.context,
        metadata_json=case_in.metadata_json or {}
    )
    db.add(case)
    dataset.num_cases += 1
    db.commit()
    db.refresh(case)
    return case

@router.delete("/cases/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_dataset_case(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    case = db.query(DatasetCase).filter(DatasetCase.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Test case not found.")
    dataset = db.query(Dataset).filter(Dataset.id == case.dataset_id).first()
    verify_project_access(dataset.project_id, user=current_user, db=db)
    
    db.delete(case)
    if dataset.num_cases > 0:
        dataset.num_cases -= 1
    db.commit()
    return None

@router.post("/validate-upload", response_model=DatasetValidationResult)
async def validate_dataset_upload(
    file: UploadFile = File(...)
):
    """
    Validates CSV or JSONL dataset file contents without committing to DB.
    Detects missing inputs, malformed records, empty lines, and returns preview.
    """
    contents = await file.read()
    filename = file.filename or "upload.jsonl"
    
    errors: List[DatasetValidationError] = []
    warnings: List[str] = []
    valid_rows = 0
    invalid_rows = 0
    preview = []

    text_data = contents.decode("utf-8", errors="replace")
    lines = [line.strip() for line in text_data.splitlines() if line.strip()]

    if not lines:
        return DatasetValidationResult(
            is_valid=False,
            total_rows=0,
            valid_rows=0,
            invalid_rows=0,
            errors=[DatasetValidationError(row_index=0, field="file", error="Uploaded file is completely empty.")],
            warnings=[],
            preview=[]
        )

    if filename.endswith(".jsonl") or filename.endswith(".json"):
        for idx, line in enumerate(lines, start=1):
            try:
                item = json.loads(line)
                if not isinstance(item, dict):
                    invalid_rows += 1
                    errors.append(DatasetValidationError(row_index=idx, field="root", error="Line is not a valid JSON object."))
                    continue
                
                input_val = item.get("input") or item.get("input_text") or item.get("query")
                if not input_val or not str(input_val).strip():
                    invalid_rows += 1
                    errors.append(DatasetValidationError(row_index=idx, field="input", error="Missing required 'input' field."))
                    continue

                valid_rows += 1
                if len(preview) < 5:
                    preview.append({
                        "input": str(input_val),
                        "expected_output": item.get("expected_output") or item.get("ground_truth") or "",
                        "context": item.get("context", "")
                    })
            except Exception as e:
                invalid_rows += 1
                errors.append(DatasetValidationError(row_index=idx, field="json", error=f"Malformed JSON: {str(e)}"))

    elif filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text_data))
        for idx, row in enumerate(reader, start=1):
            input_val = row.get("input") or row.get("input_text") or row.get("query") or row.get("question")
            if not input_val or not str(input_val).strip():
                invalid_rows += 1
                errors.append(DatasetValidationError(row_index=idx, field="input", error="Row missing 'input' or 'question' column."))
                continue

            valid_rows += 1
            if len(preview) < 5:
                preview.append({
                    "input": str(input_val),
                    "expected_output": row.get("expected_output") or row.get("ground_truth") or row.get("answer") or "",
                    "context": row.get("context", "")
                })

    is_valid = invalid_rows == 0 and valid_rows > 0
    return DatasetValidationResult(
        is_valid=is_valid,
        total_rows=valid_rows + invalid_rows,
        valid_rows=valid_rows,
        invalid_rows=invalid_rows,
        errors=errors[:50],  # Return first 50 errors
        warnings=warnings,
        preview=preview
    )

@router.post("/upload", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    project_id: int = Form(...),
    name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_project_access(project_id, user=current_user, db=db)

    contents = await file.read()
    filename = file.filename or "uploaded.jsonl"
    text_data = contents.decode("utf-8", errors="replace")

    cases_to_add = []
    if filename.endswith(".csv"):
        reader = csv.DictReader(io.StringIO(text_data))
        for row in reader:
            inp = row.get("input") or row.get("input_text") or row.get("query") or row.get("question")
            if inp:
                cases_to_add.append(DatasetCase(
                    input_text=str(inp).strip(),
                    expected_output=row.get("expected_output") or row.get("ground_truth") or row.get("answer"),
                    context=row.get("context"),
                    metadata_json={}
                ))
    else:
        # JSONL
        for line in text_data.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                inp = item.get("input") or item.get("input_text") or item.get("query")
                if inp:
                    cases_to_add.append(DatasetCase(
                        input_text=str(inp).strip(),
                        expected_output=item.get("expected_output") or item.get("ground_truth"),
                        context=item.get("context"),
                        metadata_json=item.get("metadata", {})
                    ))
            except Exception:
                continue

    if not cases_to_add:
        raise HTTPException(
            status_code=400,
            detail="No valid test cases found in file. Ensure file contains 'input' fields."
        )

    dataset = Dataset(
        project_id=project_id,
        name=name,
        description=description,
        file_format="csv" if filename.endswith(".csv") else "jsonl",
        num_cases=len(cases_to_add)
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    for c in cases_to_add:
        c.dataset_id = dataset.id
        db.add(c)
    db.commit()
    db.refresh(dataset)

    return dataset

@router.get("/{dataset_id}/download")
def download_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found.")
    verify_project_access(dataset.project_id, user=current_user, db=db)

    cases = db.query(DatasetCase).filter(DatasetCase.dataset_id == dataset.id).all()
    lines = []
    for c in cases:
        lines.append(json.dumps({
            "input": c.input_text,
            "expected_output": c.expected_output,
            "context": c.context,
            "metadata": c.metadata_json or {}
        }))

    return PlainTextResponse(
        content="\n".join(lines),
        media_type="application/x-jsonlines",
        headers={"Content-Disposition": f"attachment; filename=dataset_{dataset.id}.jsonl"}
    )
