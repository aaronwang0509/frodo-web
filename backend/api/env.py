# api/env.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from core import db
from core.security import get_current_user
from models import db_models
from models.env_models import EnvironmentCreate, EnvironmentUpdate
from core.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()

@router.get("/", response_model=list[db_models.Environment])
def list_envs(
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    List all environments owned by the current user.
    """
    envs = session.exec(
        select(db_models.Environment).where(
            db_models.Environment.user_profile_id == current_user.id
        )
    ).all()
    return envs


@router.post("/", response_model=db_models.Environment)
def create_env(
    payload: EnvironmentCreate,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Create a new environment for the current user.
    """
    exists = session.exec(
        select(db_models.Environment).where(
            (db_models.Environment.user_profile_id == current_user.id) &
            (db_models.Environment.name == payload.name)
        )
    ).first()
    if exists:
        raise HTTPException(status_code=409, detail="Environment name already exists for this user.")

    env = db_models.Environment(**payload.model_dump(), user_profile_id=current_user.id)
    session.add(env)
    session.commit()
    session.refresh(env)
    logger.info(f"Environment '{payload.name}' created for user_id={current_user.id}")
    return env

@router.get("/{env_name}", response_model=db_models.Environment)
def get_env(
    env_name: str,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Get a specific environment by name for the current user.
    """
    env = session.exec(
        select(db_models.Environment).where(
            (db_models.Environment.user_profile_id == current_user.id) &
            (db_models.Environment.name == env_name)
        )
    ).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found.")
    return env

@router.patch("/{env_name}", response_model=db_models.Environment)
def update_env(
    env_name: str,
    payload: EnvironmentUpdate,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Update an existing environment by name for the current user.
    """
    env = session.exec(
        select(db_models.Environment).where(
            (db_models.Environment.user_profile_id == current_user.id) &
            (db_models.Environment.name == env_name)
        )
    ).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found.")

    env_data = payload.model_dump(exclude_unset=True)
    for key, value in env_data.items():
        setattr(env, key, value)

    session.add(env)
    session.commit()
    session.refresh(env)
    logger.info(f"Environment '{env_name}' updated for user_id={current_user.id}")
    return env

@router.delete("/{env_name}", response_model=dict)
def delete_env(
    env_name: str,
    session: Session = Depends(db.get_session),
    current_user: db_models.UserProfile = Depends(get_current_user)
):
    """
    Delete an environment by name for the current user.
    """
    env = session.exec(
        select(db_models.Environment).where(
            (db_models.Environment.user_profile_id == current_user.id) &
            (db_models.Environment.name == env_name)
        )
    ).first()
    if not env:
        raise HTTPException(status_code=404, detail="Environment not found.")

    session.delete(env)
    session.commit()
    logger.info(f"Environment '{env_name}' deleted for user_id={current_user.id}")
    return {"detail": "Environment deleted successfully."}
