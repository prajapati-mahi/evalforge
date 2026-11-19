import os
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.experiment import Experiment
from app.models.user import User
from app.schemas.report import ReportGenerateRequest, ReportResponse
from app.api.deps import get_current_user, verify_project_access
from app.reports.generator import generate_pdf_report, generate_csv_report, REPORTS_DIR

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.post("", response_model=ReportResponse)
def create_report(
    req: ReportGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == req.experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)

    if req.format.lower() == "csv":
        filepath = generate_csv_report(db, exp.id)
    else:
        filepath = generate_pdf_report(db, exp.id)

    filename = os.path.basename(filepath)
    file_size = os.path.getsize(filepath)

    return ReportResponse(
        report_id=filename,
        experiment_id=exp.id,
        filename=filename,
        download_url=f"/api/v1/reports/{filename}/download",
        generated_at=str(os.path.getmtime(filepath)),
        file_size_bytes=file_size
    )

@router.get("/{filename}/download")
def download_report_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    safe_filename = os.path.basename(filename)
    filepath = os.path.join(REPORTS_DIR, safe_filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report file not found.")

    media_type = "application/pdf" if safe_filename.endswith(".pdf") else "text/csv"
    return FileResponse(
        path=filepath,
        filename=safe_filename,
        media_type=media_type
    )
