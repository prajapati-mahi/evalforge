from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.project import Project
from app.models.dataset import Dataset
from app.models.experiment import Experiment
from app.models.trace import Trace
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.api.deps import get_current_user, verify_project_access

router = APIRouter(prefix="/projects", tags=["Projects"])

@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    projects = (
        db.query(Project)
        .filter(Project.owner_id == current_user.id)
        .order_by(Project.created_at.desc())
        .all()
    )
    result = []
    for p in projects:
        num_ds = db.query(Dataset).filter(Dataset.project_id == p.id).count()
        num_exp = db.query(Experiment).filter(Experiment.project_id == p.id).count()
        num_tr = db.query(Trace).filter(Trace.project_id == p.id).count()
        res_item = ProjectResponse.model_validate(p)
        res_item.num_datasets = num_ds
        res_item.num_experiments = num_exp
        res_item.num_traces = num_tr
        result.append(res_item)
    return result

@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = Project(
        name=project_in.name,
        description=project_in.description,
        project_type=project_in.project_type,
        default_model=project_in.default_model,
        owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    
    res = ProjectResponse.model_validate(project)
    res.num_datasets = 0
    res.num_experiments = 0
    res.num_traces = 0
    return res

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = verify_project_access(project_id, user=current_user, db=db)
    res = ProjectResponse.model_validate(project)
    res.num_datasets = db.query(Dataset).filter(Dataset.project_id == project.id).count()
    res.num_experiments = db.query(Experiment).filter(Experiment.project_id == project.id).count()
    res.num_traces = db.query(Trace).filter(Trace.project_id == project.id).count()
    return res

@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_in: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = verify_project_access(project_id, user=current_user, db=db)
    if project_in.name is not None:
        project.name = project_in.name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.project_type is not None:
        project.project_type = project_in.project_type
    if project_in.default_model is not None:
        project.default_model = project_in.default_model

    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)

@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = verify_project_access(project_id, user=current_user, db=db)
    db.delete(project)
    db.commit()
    return None
