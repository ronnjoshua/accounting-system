from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User, Role, UserInvite
from app.schemas.user import UserCreate, AcceptInvite
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    generate_invite_token
)


def authenticate_user(
    db: Session, email: str, password: str
) -> Optional[User]:
    result = db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    return user


def create_user_from_invite(
    db: Session, invite: UserInvite, data: AcceptInvite
) -> User:
    user = User(
        email=invite.email,
        hashed_password=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        is_active=True
    )

    # Assign role from invite
    result = db.execute(select(Role).where(Role.id == invite.role_id))
    role = result.scalar_one_or_none()
    if role:
        user.roles.append(role)

    db.add(user)

    # Mark invite as accepted
    invite.accepted_at = datetime.utcnow()

    db.commit()
    db.refresh(user)
    return user


def create_invite(
    db: Session,
    email: str,
    role_id: int,
    invited_by_id: int,
    expires_in_days: int = 7
) -> UserInvite:
    # Check if user already exists
    result = db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise ValueError("User with this email already exists")

    # Check if invite already exists
    result = db.execute(select(UserInvite).where(UserInvite.email == email))
    existing_invite = result.scalar_one_or_none()
    if existing_invite and not existing_invite.accepted_at:
        # Delete old invite
        db.delete(existing_invite)
        db.commit()

    invite = UserInvite(
        email=email,
        token=generate_invite_token(),
        role_id=role_id,
        invited_by_id=invited_by_id,
        expires_at=datetime.utcnow() + timedelta(days=expires_in_days)
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


def get_invite_by_token(db: Session, token: str) -> Optional[UserInvite]:
    result = db.execute(
        select(UserInvite).where(
            UserInvite.token == token,
            UserInvite.accepted_at.is_(None),
            UserInvite.expires_at > datetime.utcnow()
        )
    )
    return result.scalar_one_or_none()


def generate_tokens(user: User) -> dict:
    access_token = create_access_token(
        subject=user.id,
        additional_claims={"email": user.email}
    )
    refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }
