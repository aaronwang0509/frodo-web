# models/db_models.py
import uuid
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from typing import Optional, List
from datetime import datetime, UTC
from sqlalchemy import Column, JSON, String

class IdentityUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str
    issuer: str = "local-idp"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user_profile: Optional["UserProfile"] = Relationship(back_populates="identity_user")

    __table_args__ = (UniqueConstraint("subject", "issuer"),)

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="identityuser.id", unique=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = None
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    identity_user: Optional[IdentityUser] = Relationship(back_populates="user_profile")
    environments: List["Environment"] = Relationship(back_populates="user_profile")
    esv_variables: List["EsvVariable"] = Relationship(back_populates="user_profile")
    jobs: List["Job"] = Relationship(back_populates="user_profile")

class Environment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    frodo: Optional[str] = None
    platformUrl: str
    serviceAccountID: str
    serviceAccountJWK: dict = Field(sa_column=Column(JSON))
    expSeconds: int = 899
    scope: str
    proxy: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user_profile_id: int = Field(foreign_key="userprofile.id")

    user_profile: Optional[UserProfile] = Relationship(back_populates="environments")
    esv_variable_values: List["EsvVariableValue"] = Relationship(back_populates="environment")

class EsvVariable(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = None
    expressionType: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user_profile_id: int = Field(foreign_key="userprofile.id")

    user_profile: Optional[UserProfile] = Relationship(back_populates="esv_variables")
    values: List["EsvVariableValue"] = Relationship(back_populates="variable")

    __table_args__ = (UniqueConstraint("name", "user_profile_id"),)

class EsvVariableValue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    value: str

    variable_id: int = Field(foreign_key="esvvariable.id")
    environment_id: int = Field(foreign_key="environment.id")

    variable: Optional[EsvVariable] = Relationship(back_populates="values")
    environment: Optional[Environment] = Relationship(back_populates="esv_variable_values")

    __table_args__ = (UniqueConstraint("variable_id", "environment_id"),)

class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        sa_column=Column("job_id", String, unique=True, nullable=False)
    )
    job_type: str  # e.g., 'push', 'pull'
    status: str = Field(default="pending")  # pending, running, success, failed
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user_profile_id: int = Field(foreign_key="userprofile.id")

    user_profile: Optional[UserProfile] = Relationship(back_populates="jobs")