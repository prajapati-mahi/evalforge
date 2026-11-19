from fastapi import APIRouter
from app.api.v1 import (
    auth,
    projects,
    datasets,
    prompts,
    providers,
    experiments,
    evaluations,
    comparisons,
    traces,
    reports,
    dashboard,
    health
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(datasets.router)
api_router.include_router(prompts.router)
api_router.include_router(providers.router)
api_router.include_router(experiments.router)
api_router.include_router(evaluations.router)
api_router.include_router(comparisons.router)
api_router.include_router(traces.router)
api_router.include_router(reports.router)
api_router.include_router(dashboard.router)
api_router.include_router(health.router)
