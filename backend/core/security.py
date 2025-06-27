# core/security.py
import os
from datetime import datetime, timedelta, UTC
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from cryptography.fernet import Fernet
from core.settings import settings

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
