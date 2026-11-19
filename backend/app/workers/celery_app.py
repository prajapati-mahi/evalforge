import asyncio
from celery import Celery
from app.core.config import settings
from app.core.database import SessionLocal

celery_app = Celery(
    "evalforge_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_concurrency=4
)

@celery_app.task(bind=True, name="run_experiment_task")
def run_experiment_task(self, experiment_id: int):
    """Celery background task for experiment execution."""
    from app.experiments.runner import execute_experiment_pipeline
    
    db = SessionLocal()
    try:
        asyncio.run(execute_experiment_pipeline(
            db=db,
            experiment_id=experiment_id,
            background_job_id=self.request.id
        ))
    finally:
        db.close()

def dispatch_experiment_execution(
    experiment_id: int,
    background_tasks=None
) -> str:
    """
    Intelligently dispatch experiment run:
    Tries Celery first if enabled and reachable; otherwise falls back to
    asynchronous background executor without requiring Redis locally.
    """
    import uuid
    task_id = str(uuid.uuid4())
    
    # Check if Celery is preferred and Redis is active
    if not settings.ENABLE_INLINE_WORKER:
        try:
            result = run_experiment_task.delay(experiment_id)
            return result.id
        except Exception:
            pass  # Fall back to inline background task

    # Inline background execution using asyncio
    async def _async_runner():
        from app.experiments.runner import execute_experiment_pipeline
        db = SessionLocal()
        try:
            await execute_experiment_pipeline(
                db=db,
                experiment_id=experiment_id,
                background_job_id=task_id
            )
        finally:
            db.close()

    if background_tasks:
        background_tasks.add_task(lambda: asyncio.run(_async_runner()))
    else:
        # Schedule in event loop if available or spawn thread
        import threading
        t = threading.Thread(target=lambda: asyncio.run(_async_runner()), daemon=True)
        t.start()

    return task_id
