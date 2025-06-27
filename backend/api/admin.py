# api/admin.py
from fastapi import APIRouter, Depends, HTTPException
from models import db_models, user_models
from sqlmodel import Session, select
from core import db, security
from .utils import require_admin

router = APIRouter()

@router.get("/users", response_model=list[user_models.UserProfileOut])
def list_users(
    admin: db_models.IdentityUser = Depends(require_admin),
    session: Session = Depends(db.get_session)
):
    return session.exec(select(db_models.UserProfile)).all()

@router.post("/users", response_model=user_models.UserProfileOut)
def provision_user(
    req: user_models.UserProvisioningRequest,
    admin: db_models.IdentityUser = Depends(require_admin),
    session: Session = Depends(db.get_session)
):
    # Check if IdentityUser exists
    identity_user = session.exec(
        select(db_models.IdentityUser).where(
            (db_models.IdentityUser.subject == req.subject) &
            (db_models.IdentityUser.issuer == req.issuer)
        )
    ).first()

    if identity_user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Create IdentityUser
    identity_user = db_models.IdentityUser(subject=req.subject, issuer=req.issuer)
    session.add(identity_user)
    session.commit()
    session.refresh(identity_user)

    # Create UserProfile
    profile = db_models.UserProfile(
        user_id=identity_user.id,
        username=req.username,
        email=req.email,
        is_active=req.is_active,
        role=req.role
    )
    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile

@router.patch("/users/{user_id}", response_model=user_models.UserProfileOut)
def update_user_profile(
    user_id: int,
    payload: user_models.UserProfileUpdate,
    admin: db_models.IdentityUser = Depends(require_admin),
    session: Session = Depends(db.get_session)
):
    profile = session.exec(
        select(db_models.UserProfile).where(db_models.UserProfile.user_id == user_id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(profile, key, value)

    session.add(profile)
    session.commit()
    session.refresh(profile)

    return profile

@router.delete("/users/{user_id}", response_model=dict)
def delete_user(
    user_id: int,
    admin: db_models.IdentityUser = Depends(require_admin),
    session: Session = Depends(db.get_session)
):
    # Fetch both IdentityUser and UserProfile
    profile = session.exec(
        select(db_models.UserProfile).where(db_models.UserProfile.user_id == user_id)
    ).first()
    
    user = session.exec(
        select(db_models.IdentityUser).where(db_models.IdentityUser.id == user_id)
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="IdentityUser not found")

    # Delete profile if exists
    if profile:
        session.delete(profile)

    # Delete identity user
    session.delete(user)
    session.commit()

    return {"msg": f"User {user_id} deleted successfully"}
