from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.experiment import Experiment, ExperimentRun, TestCaseRun
from app.models.dataset import Dataset, DatasetCase
from app.models.job import BackgroundJob
from app.models.user import User
from app.schemas.experiment import (
    ExperimentCreate, ExperimentResponse, ExperimentRunResponse, TestCaseRunResponse
)
from app.api.deps import get_current_user, verify_project_access
from app.workers.celery_app import dispatch_experiment_execution

router = APIRouter(prefix="/experiments", tags=["Experiments"])

@router.get("", response_model=List[ExperimentResponse])
def list_experiments(
    project_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Experiment)
    if project_id:
        verify_project_access(project_id, user=current_user, db=db)
        query = query.filter(Experiment.project_id == project_id)
    else:
        from app.models.project import Project
        user_proj_ids = [p.id for p in db.query(Project.id).filter(Project.owner_id == current_user.id).all()]
        query = query.filter(Experiment.project_id.in_(user_proj_ids))

    return query.order_by(Experiment.created_at.desc()).all()

@router.post("", response_model=ExperimentResponse, status_code=status.HTTP_201_CREATED)
def create_experiment(
    exp_in: ExperimentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_project_access(exp_in.project_id, user=current_user, db=db)
    
    dataset = db.query(Dataset).filter(Dataset.id == exp_in.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=400, detail="Specified dataset not found.")

    num_cases = db.query(DatasetCase).filter(DatasetCase.dataset_id == dataset.id).count()
    total_expected = num_cases * len(exp_in.config.models)

    experiment = Experiment(
        project_id=exp_in.project_id,
        name=exp_in.name,
        description=exp_in.description,
        dataset_id=exp_in.dataset_id,
        prompt_version_id=exp_in.prompt_version_id,
        config_json=exp_in.config.model_dump(),
        created_by=current_user.id,
        status="pending",
        total_cases=total_expected,
        processed_cases=0
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return experiment

@router.post("/{experiment_id}/run", response_model=ExperimentResponse)
def run_experiment(
    experiment_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)

    if exp.status in ("running", "queued"):
        raise HTTPException(status_code=400, detail=f"Experiment is already in {exp.status} status.")

    exp.status = "queued"
    db.commit()

    task_id = dispatch_experiment_execution(experiment_id=exp.id, background_tasks=background_tasks)
    
    # Track background job
    job = BackgroundJob(
        task_id=task_id,
        job_type="experiment_run",
        status="queued",
        progress=0.0,
        payload_json={"experiment_id": exp.id, "name": exp.name}
    )
    db.add(job)
    db.commit()

    db.refresh(exp)
    return exp

@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)
    return exp

@router.get("/{experiment_id}/results")
def get_experiment_results(
    experiment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)

    runs = db.query(ExperimentRun).filter(ExperimentRun.experiment_id == exp.id).all()
    results = []
    for r in runs:
        case_runs = (
            db.query(TestCaseRun)
            .filter(TestCaseRun.experiment_run_id == r.id)
            .order_by(TestCaseRun.id.asc())
            .all()
        )
        run_data = ExperimentRunResponse.model_validate(r)
        run_data.test_case_runs = [TestCaseRunResponse.model_validate(cr) for cr in case_runs]
        results.append(run_data)

    return {
        "experiment_id": exp.id,
        "name": exp.name,
        "status": exp.status,
        "total_cases": exp.total_cases,
        "processed_cases": exp.processed_cases,
        "runs": results
    }

@router.post("/{experiment_id}/cancel")
def cancel_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)

    if exp.status not in ("running", "queued", "pending"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel experiment in '{exp.status}' status.")

    exp.status = "cancelled"
    exp.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "cancelled", "message": "Experiment execution cancelled."}

@router.delete("/{experiment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    exp = db.query(Experiment).filter(Experiment.id == experiment_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Experiment not found.")
    verify_project_access(exp.project_id, user=current_user, db=db)
    db.delete(exp)
    db.commit()
    return None
