# api/paic.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from core import db
from core.security import get_current_user
from core.logger import get_logger
from core.job import run_job_in_background
from core.services.update_and_push_service import run_update_and_push
from models import db_models

logger = get_logger(__name__)

router = APIRouter()

@router.post("/update-and-push/{env_name}", status_code=200)
def update_and_push_api(
    env_name: str,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Run Frodo export and push updates for the given environment.
    """
    job_id = run_job_in_background(
        job_type="update_and_push",
        job_fn=lambda: run_update_and_push(
            env_name=env_name,
            session=session,
            current_user=current_user
        ),
        session=session,
        current_user=current_user
    )

    return {"job_id": job_id}