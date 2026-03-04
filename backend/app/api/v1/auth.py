from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.schemas.user import (
    UserLogin, TokenResponse, UserResponse,
    UserInviteCreate, UserInviteResponse, AcceptInvite
)
from app.services.auth import (
    authenticate_user, create_invite, get_invite_by_token,
    create_user_from_invite, generate_tokens
)
from app.services.audit import create_audit_log
from app.models.user import User

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, data.email, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Create audit log
    create_audit_log(
        db,
        action="login",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        user_email=user.email,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )

    tokens = generate_tokens(user)
    return TokenResponse(**tokens, user=UserResponse.model_validate(user))


@router.post("/invite", response_model=UserInviteResponse)
def invite_user(
    data: UserInviteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Only admins can invite
    user_roles = [role.name for role in current_user.roles]
    if "admin" not in user_roles and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can invite users"
        )

    try:
        invite = create_invite(
            db, data.email, data.role_id, current_user.id
        )
        return invite
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/accept-invite", response_model=TokenResponse)
def accept_invite(
    data: AcceptInvite,
    request: Request,
    db: Session = Depends(get_db)
):
    invite = get_invite_by_token(db, data.token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite token"
        )

    user = create_user_from_invite(db, invite, data)

    # Create audit log
    create_audit_log(
        db,
        action="accept_invite",
        entity_type="user",
        entity_id=user.id,
        user_id=user.id,
        user_email=user.email,
        ip_address=request.client.host if request.client else None
    )

    tokens = generate_tokens(user)
    return TokenResponse(**tokens, user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    return current_user


@router.get("/verify-invite/{token}")
def verify_invite(
    token: str,
    db: Session = Depends(get_db)
):
    invite = get_invite_by_token(db, token)
    if not invite:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired invite token"
        )
    return {"email": invite.email, "valid": True}
