"""
Router: /users
==============

User management endpoints – restricted to admins and superusers.

Endpoint                        | Required global role
--------------------------------|---------------------
GET  /users/                    | admin or superuser
GET  /users/{id}                | admin or superuser (or self)
POST /users/                    | admin or superuser
PUT  /users/{id}                | admin or superuser (limited self-edit)
DELETE /users/{id}              | superuser only
PUT  /users/{id}/promote        | superuser only
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.permissions import require_global_admin, require_superuser
from app.core.security import hash_password
from app.database import get_db
from app.models.project_membership import ProjectMembership
from app.models.user import GlobalRole, User
from app.routers.auth import get_current_user
from app.schemas.membership import UserCreate, UserMembershipInfo, UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="List all users (admin+)",
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_global_admin()),
) -> list[UserResponse]:
    result = await db.execute(
        select(User)
        .where(User.is_deleted.is_(False))
        .order_by(User.username)
        .options(
            selectinload(User.memberships).selectinload(ProjectMembership.project)
        )
    )
    users = result.scalars().all()
    return [
        UserResponse(
            **{k: getattr(u, k) for k in ("id", "username", "email", "full_name",
                                           "is_active", "global_role", "is_admin",
                                           "created_at", "updated_at")},
            memberships=[UserMembershipInfo.from_membership(m) for m in u.memberships],
        )
        for u in users
    ]


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a user by ID (admin+ or self)",
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    # Self-access is always allowed
    if current_user.id != user_id:
        if current_user.global_role not in (GlobalRole.admin, GlobalRole.superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin or superuser role required.",
            )

    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found.")
    return user


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user (admin+)",
)
async def create_user(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_global_admin()),
) -> User:
    # Only superusers may create other superusers
    if payload.global_role == GlobalRole.superuser:
        if current_user.global_role != GlobalRole.superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers may create superuser accounts.",
            )

    # Check uniqueness
    dup = await db.execute(
        select(User).where(
            (User.username == payload.username) | (User.email == payload.email),
            User.is_deleted.is_(False),
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email already in use.",
        )

    user = User(
        username=payload.username,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        global_role=payload.global_role,
        is_admin=(payload.global_role in (GlobalRole.admin, GlobalRole.superuser)),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user (admin+ or self)",
)
async def update_user(
    user_id: UUID,
    payload: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    is_self = current_user.id == user_id
    is_privileged = current_user.global_role in (GlobalRole.admin, GlobalRole.superuser)

    if not is_self and not is_privileged:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")

    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found.")

    # Role changes require admin+; only superusers can grant superuser
    if payload.global_role is not None:
        if not is_privileged:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot change your own role.",
            )
        if payload.global_role == GlobalRole.superuser and current_user.global_role != GlobalRole.superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers may grant superuser role.",
            )
        user.global_role = payload.global_role
        user.is_admin = payload.global_role in (GlobalRole.admin, GlobalRole.superuser)

    if payload.email     is not None: user.email     = payload.email
    if payload.full_name is not None: user.full_name = payload.full_name
    if payload.is_active is not None:
        if not is_privileged:
            raise HTTPException(status_code=403, detail="Cannot change activation status.")
        user.is_active = payload.is_active
    if payload.password  is not None:
        user.hashed_password = hash_password(payload.password)

    await db.commit()
    await db.refresh(user)
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a user (superuser only)",
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_superuser()),
) -> None:
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account.",
        )

    user = await db.get(User, user_id)
    if not user or user.is_deleted:
        raise HTTPException(status_code=404, detail="User not found.")

    from datetime import datetime, timezone
    user.is_deleted = True
    user.deleted_at = datetime.now(timezone.utc)
    user.is_active  = False
    await db.commit()
