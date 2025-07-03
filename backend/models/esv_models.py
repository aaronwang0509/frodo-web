# models/esv.models.py
from pydantic import BaseModel
from typing import Optional, Dict

class EsvVariableResponse(BaseModel):
    name: str
    description: Optional[str]
    expressionType: Optional[str]
    values: Optional[Dict[str, str]]

class EsvVariableCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    expressionType: Optional[str]
    values: Optional[Dict[str, str]]

class EsvVariableUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    expressionType: Optional[str] = None
    values: Optional[Dict[str, str]] = None

class EsvVariableDelete(BaseModel):
    name: str
    description: Optional[str] = None
    expressionType: Optional[str] = None
    values: Optional[Dict[str, str]] = None

class EsvVariablePerEnv(BaseModel):
    description: Optional[str] = None
    expressionType: Optional[str] = None
    value: Optional[str] = None