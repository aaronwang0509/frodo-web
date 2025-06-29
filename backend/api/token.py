# api/token.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from core.db import get_session
from core.logger import get_logger
from core.security import get_current_user
from models.db_models import Environment, UserProfile
from core.frodo.get_token import get_service_account_access_token

logger = get_logger(__name__)

router = APIRouter()

@router.post("/{env_name}")
def generate_service_account_token(
    env_name: str,
    current_user: UserProfile = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Look up environment for this user
    statement = select(Environment).where(
        Environment.user_profile_id == current_user.id,
        Environment.name == env_name
    )
    environment = session.exec(statement).first()

    if not environment:
        logger.warning(f"Environment '{env_name}' not found for user_id={current_user.id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Environment '{env_name}' not found"
        )

    # Call your frodo lib
    token = get_service_account_access_token(
        platform_url=environment.platformUrl,
        service_account_id=environment.serviceAccountID,
        jwk_dict=environment.serviceAccountJWK,
        exp_seconds=environment.expSeconds,
        scope=environment.scope,
        proxy_url=environment.proxy
    )

    logger.info(
        f"Issued new service account token for env='{env_name}'",
        extra={"user_id": current_user.id}
    )

    return {
        "access_token": token,
        "scope": environment.scope,
        "token_type": "Bearer",
        "expires_in": environment.expSeconds
    }