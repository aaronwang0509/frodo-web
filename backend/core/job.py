# core/services/job_service.py
import threading
from sqlmodel import Session, select
from typing import Optional, Callable, Any
from core.logger import get_logger
from models import db_models
from datetime import datetime, UTC

logger = get_logger(__name__)

def create_job(
    session: Session,
    current_user: db_models.UserProfile,
    job_type: str
) -> db_models.Job:
    """
    Create a new Job record with status 'pending'.
    """
    job = db_models.Job(
        job_type=job_type,
        status="pending",
        user_profile_id=current_user.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC)
    )
    session.add(job)
    session.commit()
    session.refresh(job)
    return job

def update_job_status(
    session: Session,
    current_user: db_models.UserProfile,
    job_id: str,
    status: str,
    result: Optional[dict] = None
) -> db_models.Job:
    statement = select(db_models.Job).where(
        db_models.Job.job_id == job_id,
        db_models.Job.user_profile_id == current_user.id
    )
    job = session.exec(statement).first()
    if not job:
        raise ValueError(f"Job {job_id} not found.")

    job.status = status
    if result is not None:
        job.result = result
    job.updated_at = datetime.now(UTC)

    session.add(job)
    session.commit()
    session.refresh(job)
    return job

def get_job_status(
    session: Session,
    current_user: db_models.UserProfile,
    job_id: str
) -> str:
    statement = select(db_models.Job).where(
        db_models.Job.job_id == job_id,
        db_models.Job.user_profile_id == current_user.id
    )
    job = session.exec(statement).first()
    if not job:
        raise ValueError(f"Job {job_id} not found or access denied.")
    return job.status

def get_job_result(
    session: Session,
    current_user: db_models.UserProfile,
    job_id: str
) -> Optional[dict]:
    statement = select(db_models.Job).where(
        db_models.Job.job_id == job_id,
        db_models.Job.user_profile_id == current_user.id
    )
    job = session.exec(statement).first()
    if not job:
        raise ValueError(f"Job {job_id} not found or access denied.")
    return job.result

def run_job_in_background(
    *,
    job_type: str,
    job_fn: Callable[[], Any],
    session: Session,
    current_user: db_models.UserProfile
) -> int:
    """
    Create a Job and run the given job_fn in a background thread.
    Handles job status updates and logs automatically.
    Returns: job_id
    """

    job = create_job(
        session=session,
        current_user=current_user,
        job_type=job_type
    )

    def background_task():
        logger.info(f"Job_id={job.job_id} job_type={job_type} user_id={current_user.id} started")
        try:
            update_job_status(
                session=session,
                current_user=current_user,
                job_id=job.job_id,
                status="running"
            )

            result = job_fn()

            update_job_status(
                session=session,
                current_user=current_user,
                job_id=job.job_id,
                status="success",
                result=result
            )
            logger.info(f"Job_id={job.job_id} job_type={job_type} finished successfully")

        except Exception as e:
            logger.exception(f"Job_id={job.job_id} job_type={job_type} failed: {e}")
            update_job_status(
                session=session,
                current_user=current_user,
                job_id=job.job_id,
                status="failed",
                result={"error": str(e)}
            )

    thread = threading.Thread(target=background_task)
    thread.start()

    return job.job_id