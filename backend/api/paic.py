# api/paic.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from core import db
from core.security import get_current_user
from core.logger import get_logger
from core.frodo.update_and_push import update_and_push
from api.settings import settings
from models import db_models

logger = get_logger(__name__)

router = APIRouter()

@router.post("/{env_name}/update-and-push", status_code=200)
def run_update_and_push(
    env_name: str,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Run Frodo export and push updates for the given environment.
    """
    # Retrieve env details for current user
    env = session.exec(
        select(db_models.Environment).where(
            (db_models.Environment.user_profile_id == current_user.id) &
            (db_models.Environment.name == env_name)
        )
    ).first()

    if not env:
        raise HTTPException(status_code=404, detail="Environment not found.")

    logger.info(f"Starting update_and_push for env='{env_name}' user_id={current_user.id}")

    result = update_and_push(
        paic_config_path=settings.PAIC_CONFIG_PATH,
        env_name=env.name,
        branch_name=settings.PAIC_CONFIG_BRANCH_NAME,
        frodo_path=env.frodo,
        host_url=env.platformUrl,
        proxy_url=env.proxy,
        git_user_name=current_user.username,
        git_user_email=current_user.email
    )

    logger.info(f"update_and_push result: {result}")

    if result["overall_status"] == "success":
        if result["git_push_status"] == "success":
            return {
                "detail": f"Environment '{env_name}' exported and pushed successfully.",
                "result": result
            }
        elif result["git_push_status"] == "no_changes":
            return {
                "detail": f"Environment '{env_name}' exported successfully but no changes to push.",
                "result": result
            }

    # Handle partial failures
    if result["frodo_export_status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Frodo config export failed: {result.get('stderr')}",
        )

    if result["git_push_status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Git commit/push failed: {result.get('stderr')}",
        )

    # Unexpected state
    raise HTTPException(
        status_code=500,
        detail="Unknown error occurred during update and push.",
    )