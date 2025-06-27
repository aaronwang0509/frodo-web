# api/auth.py
from fastapi import APIRouter, HTTPException, Depends, Body
from passlib.context import CryptContext
from models.user_models import UserRegister, UserLogin, Token, TokenRefreshRequest
from core import db, security
from core.logger import logger
from sqlmodel import Session, select
from models import db_models

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register")
def register(user: UserRegister):
    users = db.load_users()
    if any(u["username"] == user.username for u in users["users"]):
        raise HTTPException(status_code=400, detail="Username already exists")

    hashed_password = pwd_context.hash(user.password)
    users["users"].append({
        "username": user.username,
        "email": user.email,
        "hashed_password": hashed_password
    })
    db.save_users(users)
    return {"msg": "Registered"}

@router.post("/login", response_model=Token)
def login(user: UserLogin, session: Session = Depends(db.get_session)):
    users = db.load_users()
    found_user = next((u for u in users["users"] if u["username"] == user.username), None)

    if not found_user or not pwd_context.verify(user.password, found_user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    subject = user.username
    issuer = "local-idp"

    # JIT provision to IdentityUser
    identity_user = session.exec(
        select(db_models.IdentityUser).where(
            (db_models.IdentityUser.subject == subject) &
            (db_models.IdentityUser.issuer == issuer)
        )
    ).first()

    if not identity_user:
        identity_user = db_models.IdentityUser(subject=subject, issuer=issuer)
        session.add(identity_user)
        session.commit()
        session.refresh(identity_user)

        logger.info(f"Provisioned IdentityUser for subject: {subject} (issuer: {issuer})")

    # JIT provision to UserProfile (with username and email)
    profile = session.exec(
        select(db_models.UserProfile).where(db_models.UserProfile.user_id == identity_user.id)
    ).first()

    if not profile:
        profile = db_models.UserProfile(
            user_id=identity_user.id,
            username=user.username,
            email=found_user.get("email", None),
            is_active=True,
            role="user"
        )
        session.add(profile)
        session.commit()

        logger.info(f"Provisioned UserProfile for user_id: {identity_user.id} ({user.username})")

    # Active check
    if not profile.is_active:
        raise HTTPException(status_code=403, detail="User is disabled")

    # Generate tokens
    access_token = security.create_access_token({"sub": subject, "iss": issuer, "role": profile.role})
    refresh_token = security.create_refresh_token({"sub": subject, "iss": issuer, "role": profile.role})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh", response_model=Token)
def refresh_token(data: TokenRefreshRequest = Body(...)):
    try:
        payload = security.decode_refresh_token(data.refresh_token)
        subject = payload.get("sub")
        issuer = payload.get("iss")
        role = payload.get("role", "user")
        if not subject or not issuer:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        new_access_token = security.create_access_token({"sub": subject, "iss": issuer, "role": role})
        return {
            "access_token": new_access_token,
            "refresh_token": data.refresh_token,
            "token_type": "bearer"
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
