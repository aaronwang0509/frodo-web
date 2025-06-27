# models/business_models.py
# from pydantic import BaseModel
# from typing import List, Optional
# from datetime import datetime

# class DummyRequest(BaseModel):
#     dummy_param: str

# class UserProfileOut(BaseModel):
#     id: int
#     user_id: int
#     username: str
#     email: Optional[str]
#     role: str
#     is_active: bool
#     created_at: datetime

#     class Config:
#         orm_mode = True

# # For provisioning a brand new user (creates IdentityUser + UserProfile)
# class UserProvisioningRequest(BaseModel):
#     subject: str
#     issuer: str = "local-idp"
#     username: str
#     email: Optional[str]
#     is_active: bool = True
#     role: str = "user"

# # For updating profile fields (on existing user)
# class UserProfileUpdate(BaseModel):
#     email: Optional[str] = None
#     is_active: Optional[bool] = None
#     role: Optional[str] = None

# class UserProfileCreate(BaseModel):
#     user_id: int
#     username: str
#     email: Optional[str] = None
#     role: str = "user"
#     is_active: bool = True

# class ConnectionCreate(BaseModel):
#     name: str
#     hostname: str
#     port: int
#     bind_dn: str
#     password: str
#     use_ssl: bool

# class ConnectionOut(BaseModel):
#     id: int
#     name: str
#     hostname: str
#     port: int
#     bind_dn: str
#     use_ssl: bool

# class ConnectionUpdate(BaseModel):
#     name: Optional[str] = None
#     hostname: Optional[str] = None
#     port: Optional[int] = None
#     bind_dn: Optional[str] = None
#     password: Optional[str] = None
#     use_ssl: Optional[bool] = None

# class LDAPSearchRequest(BaseModel):
#     connection_id: int
#     base_dn: str
#     filter: str
#     attributes: Optional[List[str]] = None

# class LDAPModifyRequest(BaseModel):
#     connection_id: int
#     dn: str
#     changes: List[dict]
