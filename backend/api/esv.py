# api/esv.py
from fastapi import APIRouter, HTTPException, Depends, Body
from sqlmodel import Session, select
from typing import List
from core import db
from core.security import get_current_user
from core.logger import get_logger
from core.job import run_job_in_background
from models import db_models
from models.esv_models import (
    EsvVariableResponse,
    EsvVariableCreate,
    EsvVariableUpdate,
    EsvVariableDelete
)
from core.services.sync_esv_service import (
    get_variables_in_db,
    create_variables_in_db,
    update_variables_in_db,
    delete_variables_in_db,
    diff_source_vs_db_all_envs,
    diff_db_vs_source_all_envs,
    apply_pull_from_source,
    apply_push_to_source
)

logger = get_logger(__name__)

router = APIRouter()

@router.get("/variable", status_code=200, response_model=List[EsvVariableResponse])
def get_esv_variables(
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Get all ESV variables for the current user, grouped with values per environment.
    Uses the get_variables_in_db service.
    """
    logger.info(f"Fetching ESV variables for user_id={current_user.id}")

    response = get_variables_in_db(
        session=session,
        current_user=current_user
    )

    logger.info(f"Found {len(response)} ESV variables for user_id={current_user.id}")
    return response

@router.post("/variable", status_code=200, response_model=List[EsvVariableResponse])
def create_esv_variables(
    payload: List[EsvVariableCreate],
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Create ESV variables (and their values) for the current user.
    Uses the new create_variables_in_db service.
    """
    logger.info(f"Creating ESV variables for user_id={current_user.id}")

    created_vars = create_variables_in_db(
        payload=payload,
        session=session,
        current_user=current_user
    )

    logger.info(f"Created {len(created_vars)} ESV variables for user_id={current_user.id}")

    return created_vars

@router.patch("/variable", status_code=200, response_model=List[EsvVariableResponse])
def update_esv_variables(
    payload: List[EsvVariableUpdate],
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Update ESV variables and their values for the current user.
    """
    logger.info(f"Updating ESV variables for user_id={current_user.id}")

    updated_vars = update_variables_in_db(
        payload=payload,
        session=session,
        current_user=current_user
    )

    logger.info(f"Updated {len(updated_vars)} ESV variables for user_id={current_user.id}")

    return updated_vars

@router.delete("/variable", status_code=200, response_model=List[EsvVariableResponse])
def delete_esv_variables(
    payload: List[EsvVariableDelete],
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Delete ESV variables (and/or their specific values) for the current user.
    - If 'values' is provided, only those env values are deleted.
    - If no values remain, the variable is deleted entirely.
    """
    logger.info(f"Deleting ESV variables for user_id={current_user.id}")

    deleted_vars = delete_variables_in_db(
        payload=payload,
        session=session,
        current_user=current_user
    )

    logger.info(f"Deleted {len(deleted_vars)} ESV variables/values for user_id={current_user.id}")

    return deleted_vars

@router.get("/variable/preview-pull", status_code=200)
def preview_pull_esv_variables(
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Preview what will change in the DB if you pull variables from the local source.
    Shows create/update/delete actions.
    """
    logger.info(f"Running pull diff for user_id={current_user.id}")

    diff_result = diff_source_vs_db_all_envs(
        session=session,
        current_user=current_user
    )

    logger.info(f"Pull diff result: {diff_result}")
    return diff_result

@router.get("/variable/preview-push", status_code=200)
def preview_push_esv_variables(
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Preview what will change in the source if you push variables from the DB.
    Shows create/update/delete actions.
    """
    logger.info(f"Running push diff for user_id={current_user.id}")

    diff_result = diff_db_vs_source_all_envs(
        session=session,
        current_user=current_user
    )

    logger.info(f"Push diff result: {diff_result}")
    return diff_result

@router.post("/variable/pull", status_code=200)
def pull_esv_variables(
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Actually perform the pull sync, applying create/update/delete actions.
    """
    logger.info(f"Running pull sync for user_id={current_user.id}")
    return apply_pull_from_source(session, current_user)

@router.post("/variable/push/{env_name}", status_code=200)
def push_esv_variables(
    env_name: str,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Actually perform the push sync, applying create/update/delete actions
    for the given env_name.
    """
    job_id = run_job_in_background(
        job_type="push_esv_variables",
        job_fn=lambda: apply_push_to_source(
            env_name=env_name,
            session=session,
            current_user=current_user
        ),
        session=session,
        current_user=current_user
    )

    return {"job_id": job_id}