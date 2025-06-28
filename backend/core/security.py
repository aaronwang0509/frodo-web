# core/security.py
import os
from datetime import datetime, timedelta, UTC

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from cryptography.fernet import Fernet
from sqlmodel import Session, select

from core.settings import settings
from core import db
from models import db_models

# export environment variables
TOKEN_ALGORITHM = settings.TOKEN_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
ACCESS_TOKEN_SECRET_KEY = settings.ACCESS_TOKEN_SECRET_KEY
REFRESH_TOKEN_EXPIRE_MINUTES = settings.REFRESH_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_SECRET_KEY = settings.REFRESH_TOKEN_SECRET_KEY

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Load key from env var or fallback to local file (dev only)
FERNET_KEY = os.getenv("FERNET_KEY")
if not FERNET_KEY:
    # DEV ONLY fallback — generate once and reuse
    key_file = ".fernet.key"
    if os.path.exists(key_file):
        with open(key_file, "rb") as f:
            FERNET_KEY = f.read()
    else:
        FERNET_KEY = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(FERNET_KEY)

fernet = Fernet(FERNET_KEY)

def encrypt_password(raw_password: str) -> str:
    return fernet.encrypt(raw_password.encode()).decode()

def decrypt_password(encrypted_password: str) -> str:
    return fernet.decrypt(encrypted_password.encode()).decode()

def create_token(data: dict, expires_delta: timedelta, secret_key: str):
    to_encode = data.copy()
    expire = datetime.now(UTC) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, secret_key, algorithm=TOKEN_ALGORITHM)

def create_access_token(data: dict):
    return create_token(
        data,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
        ACCESS_TOKEN_SECRET_KEY
    )

def create_refresh_token(data: dict):
    return create_token(
        data,
        timedelta(minutes=REFRESH_TOKEN_EXPIRE_MINUTES),
        REFRESH_TOKEN_SECRET_KEY
    )

def decode_token(token: str, secret_key: str):
    return jwt.decode(token, secret_key, algorithms=[TOKEN_ALGORITHM])

def decode_access_token(token: str):
    return decode_token(token, ACCESS_TOKEN_SECRET_KEY)

def decode_refresh_token(token: str):
    return decode_token(token, REFRESH_TOKEN_SECRET_KEY)

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(db.get_session)):
    try:
        payload = decode_access_token(token)
        subject = payload.get("sub")
        issuer = payload.get("iss", "local-idp")

        if not subject:
            raise HTTPException(status_code=401, detail="Unauthorized")
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")

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

    profile = session.exec(
        select(db_models.UserProfile).where(db_models.UserProfile.user_id == identity_user.id)
    ).first()

    if not profile:
        profile = db_models.UserProfile(
            user_id=identity_user.id,
            username=subject,
            is_active=True,
            role="user"
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

    if not profile.is_active:
        raise HTTPException(status_code=403, detail="User is inactive")

    return profile

def require_admin(user: db_models.UserProfile = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user