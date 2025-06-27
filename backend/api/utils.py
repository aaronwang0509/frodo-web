# api/utils.py
from fastapi import Depends, HTTPException
from jose import JWTError
from sqlmodel import Session, select
from core import db, security
from models import db_models

def get_current_user(token: str = Depends(security.oauth2_scheme), session: Session = Depends(db.get_session)):
    try:
        payload = security.decode_token(token)
        subject = payload.get("sub")
        issuer = payload.get("iss", "local-idp")

        if not subject:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = session.exec(
        select(db_models.IdentityUser).where(
            (db_models.IdentityUser.subject == subject) &
            (db_models.IdentityUser.issuer == issuer)
        )
    ).first()

    if not user:
        user = db_models.IdentityUser(subject=subject, issuer=issuer)
        session.add(user)
        session.commit()
        session.refresh(user)

    profile = session.exec(
        select(db_models.UserProfile).where(db_models.UserProfile.user_id == user.id)
    ).first()

    if profile and not profile.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")
    
    user._role = profile.role if profile else "user"

    return user

def require_admin(user: db_models.IdentityUser = Depends(get_current_user), session: Session = Depends(db.get_session)):
    profile = session.exec(
        select(db_models.UserProfile).where(db_models.UserProfile.user_id == user.id)
    ).first()
    if not profile or profile.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user