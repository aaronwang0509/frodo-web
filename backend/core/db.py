# core/db.py
import json
import os
from sqlmodel import SQLModel, Session, create_engine
from models.db_models import IdentityUser, UserProfile
from core.settings import settings

# export environment variables
USER_FILE = settings.USER_FILE
DATABASE_URL = settings.DATABASE_URL

# === File-based user store (temporary IdP layer) ===
def load_users():
    if not os.path.exists(USER_FILE):
        return {"users": []}
    with open(USER_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f, indent=2)

# === Business SQLModel DB ===
engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)