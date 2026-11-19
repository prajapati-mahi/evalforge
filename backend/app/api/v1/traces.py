from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.trace import Trace, TraceSpan
from app.models.project import Project
from app.models.user import User
from app.schemas.trace import TraceResponse, TraceSpanResponse
from app.api.deps import get_current_user, verify_project_access

router = APIRouter(prefix="/traces", tags=["Traces & Observability"])

@router.get("", response_model=List[TraceResponse])
def list_traces(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    model_name: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Trace)
    if project_id:
        verify_project_access(project_id, user=current_user, db=db)
        query = query.filter(Trace.project_id == project_id)
    else:
        user_proj_ids = [p.id for p in db.query(Project.id).filter(Project.owner_id == current_user.id).all()]
        query = query.filter(Trace.project_id.in_(user_proj_ids))

    if status:
        query = query.filter(Trace.status == status)

    if search:
        query = query.filter(Trace.trace_name.ilike(f"%{search}%"))

    traces = query.order_by(Trace.created_at.desc()).offset(offset).limit(limit).all()
    
    results = []
    for t in traces:
        tr_data = TraceResponse.model_validate(t)
        spans = db.query(TraceSpan).filter(TraceSpan.trace_id == t.id).order_by(TraceSpan.start_time.asc()).all()
        tr_data.spans = [TraceSpanResponse.model_validate(s) for s in spans]
        results.append(tr_data)

    return results

@router.get("/{trace_id}", response_model=TraceResponse)
def get_trace(
    trace_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    trace = db.query(Trace).filter(Trace.id == trace_id).first()
    if not trace:
        raise HTTPException(status_code=404, detail="Trace record not found.")
    verify_project_access(trace.project_id, user=current_user, db=db)

    tr_data = TraceResponse.model_validate(trace)
    spans = db.query(TraceSpan).filter(TraceSpan.trace_id == trace.id).order_by(TraceSpan.start_time.asc()).all()
    tr_data.spans = [TraceSpanResponse.model_validate(s) for s in spans]
    return tr_data
