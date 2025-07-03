# models/env_models.py
from typing import Optional
from pydantic import BaseModel

class EnvironmentCreate(BaseModel):
    name: str
    frodo: Optional[str] = None
    platformUrl: str
    serviceAccountID: str
    serviceAccountJWK: dict
    expSeconds: int = 899
    scope: str
    proxy: Optional[str] = None

class EnvironmentUpdate(BaseModel):
    frodo: Optional[str] = None
    platformUrl: Optional[str] = None
    serviceAccountID: Optional[str] = None
    serviceAccountJWK: Optional[dict] = None
    expSeconds: Optional[int] = None
    scope: Optional[str] = None
    proxy: Optional[str] = None