# models/db_models.py
from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint
from typing import Optional, List
from datetime import datetime, UTC

class IdentityUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str
    issuer: str = "local-idp"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    profile: Optional["UserProfile"] = Relationship(back_populates="user")
#    connections: List["LDAPConnection"] = Relationship(back_populates="user")

    __table_args__ = (UniqueConstraint("subject", "issuer"),)

class UserProfile(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="identityuser.id", unique=True)
    username: str = Field(index=True, unique=True)
    email: Optional[str] = None
    role: str = Field(default="user")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    user: Optional[IdentityUser] = Relationship(back_populates="profile")

# class LDAPConnection(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     user_id: int = Field(foreign_key="identityuser.id")
#     name: str
#     hostname: str
#     port: int
#     bind_dn: str
#     encrypted_password: str
#     use_ssl: bool

#     user: Optional[IdentityUser] = Relationship(back_populates="connections")