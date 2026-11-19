import re
import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.prompt import Prompt, PromptVersion
from app.models.user import User
from app.schemas.prompt import (
    PromptCreate, PromptUpdate, PromptResponse,
    PromptVersionCreate, PromptVersionResponse,
    PromptTestRequest, PromptTestResponse
)
from app.api.deps import get_current_user, verify_project_access
from app.providers.factory import get_provider_adapter, infer_provider_from_model
from app.providers.base import LLMRequest
from app.core.pricing import estimate_cost

router = APIRouter(prefix="/prompts", tags=["Prompts"])

def extract_variables(text: str) -> List[str]:
    """Find all {{variable_name}} tokens in prompt text."""
    matches = re.findall(r"\{\{([a-zA-Z0-9_]+)\}\}", text)
    return sorted(list(set(matches)))

@router.get("", response_model=List[PromptResponse])
def list_prompts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_project_access(project_id, user=current_user, db=db)
    prompts = (
        db.query(Prompt)
        .filter(Prompt.project_id == project_id)
        .order_by(Prompt.updated_at.desc())
        .all()
    )
    res = []
    for p in prompts:
        pr = PromptResponse.model_validate(p)
        latest = (
            db.query(PromptVersion)
            .filter(PromptVersion.prompt_id == p.id)
            .order_by(PromptVersion.version_number.desc())
            .first()
        )
        if latest:
            pr.latest_version = PromptVersionResponse.model_validate(latest)
        res.append(pr)
    return res

@router.post("", response_model=PromptResponse, status_code=status.HTTP_201_CREATED)
def create_prompt(
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    verify_project_access(prompt_in.project_id, user=current_user, db=db)

    prompt = Prompt(
        project_id=prompt_in.project_id,
        name=prompt_in.name,
        description=prompt_in.description,
        current_version=1
    )
    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    vars_found = extract_variables(prompt_in.initial_template)
    version = PromptVersion(
        prompt_id=prompt.id,
        version_number=1,
        template_text=prompt_in.initial_template,
        system_instruction=prompt_in.system_instruction,
        variables=vars_found,
        model_parameters=prompt_in.model_parameters or {"temperature": 0.7, "max_tokens": 1024},
        change_summary="Initial prompt version"
    )
    db.add(version)
    db.commit()
    db.refresh(version)

    res = PromptResponse.model_validate(prompt)
    res.latest_version = PromptVersionResponse.model_validate(version)
    return res

@router.get("/{prompt_id}", response_model=PromptResponse)
def get_prompt(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    verify_project_access(prompt.project_id, user=current_user, db=db)

    res = PromptResponse.model_validate(prompt)
    latest = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version_number.desc())
        .first()
    )
    if latest:
        res.latest_version = PromptVersionResponse.model_validate(latest)
    return res

@router.get("/{prompt_id}/versions", response_model=List[PromptVersionResponse])
def get_prompt_versions(
    prompt_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    verify_project_access(prompt.project_id, user=current_user, db=db)

    versions = (
        db.query(PromptVersion)
        .filter(PromptVersion.prompt_id == prompt.id)
        .order_by(PromptVersion.version_number.desc())
        .all()
    )
    return versions

@router.post("/{prompt_id}/versions", response_model=PromptVersionResponse, status_code=status.HTTP_201_CREATED)
def create_prompt_version(
    prompt_id: int,
    version_in: PromptVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    prompt = db.query(Prompt).filter(Prompt.id == prompt_id).first()
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found.")
    verify_project_access(prompt.project_id, user=current_user, db=db)

    new_v_num = prompt.current_version + 1
    prompt.current_version = new_v_num

    vars_found = extract_variables(version_in.template_text)
    version = PromptVersion(
        prompt_id=prompt.id,
        version_number=new_v_num,
        template_text=version_in.template_text,
        system_instruction=version_in.system_instruction,
        variables=vars_found,
        model_parameters=version_in.model_parameters or {"temperature": 0.7, "max_tokens": 1024},
        change_summary=version_in.change_summary or f"Version {new_v_num}"
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return version

@router.post("/test", response_model=PromptTestResponse)
async def test_prompt(
    test_req: PromptTestRequest,
    current_user: User = Depends(get_current_user)
):
    """Render variables into prompt template and execute against selected model."""
    rendered = test_req.template_text
    for k, v in test_req.variables.items():
        rendered = rendered.replace(f"{{{{{k}}}}}", str(v))

    provider_name = infer_provider_from_model(test_req.model_name)
    adapter = get_provider_adapter(provider_name)

    req = LLMRequest(
        prompt=rendered,
        system_instruction=test_req.system_instruction,
        model_name=test_req.model_name,
        temperature=test_req.parameters.get("temperature", 0.7) if test_req.parameters else 0.7,
        max_tokens=test_req.parameters.get("max_tokens", 512) if test_req.parameters else 512
    )

    res = await adapter.generate(req)
    cost = estimate_cost(
        model_name=test_req.model_name,
        input_tokens=res.input_tokens,
        output_tokens=res.output_tokens
    )

    return PromptTestResponse(
        rendered_prompt=rendered,
        response_text=res.text or (res.error or "No response generated"),
        model_name=test_req.model_name,
        latency_ms=res.latency_ms,
        input_tokens=res.input_tokens,
        output_tokens=res.output_tokens,
        cost_estimate=cost
    )
