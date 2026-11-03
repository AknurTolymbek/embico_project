from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

from app.db.database import get_db
from app.core.enums import UserRole
from app.modules.auth.dependencies import get_current_user, require_admin
from app.modules.auth.models import AuthSession
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse, UserCreate, ProfileUpdate, AdminUserUpdate
from app.modules.users.service import create_user

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]
Current = Annotated[User, Depends(get_current_user)]
Admin = Annotated[User, Depends(require_admin)]


@router.get('/me', response_model=UserResponse)
async def me(user: Current):
    return user


@router.patch('/me', response_model=UserResponse)
async def profile(values: ProfileUpdate, user: Current, db: DB):
    for key, value in values.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    user.full_name = f'{user.first_name} {user.last_name}'
    await db.commit()
    return user


@router.get('/', response_model=list[UserResponse])
async def users(admin: Admin, db: DB, skip: int = Query(0, ge=0), limit: int = Query(50, ge=1, le=200)):
    return (await db.execute(select(User).order_by(User.id).offset(skip).limit(limit))).scalars().all()


@router.post('/', response_model=UserResponse, status_code=201)
async def add_user(values: UserCreate, admin: Admin, db: DB):
    user = await create_user(db, values)
    await db.commit()
    return user


@router.patch('/{user_id}', response_model=UserResponse)
async def update_user(user_id: int, values: AdminUserUpdate, admin: Admin, db: DB):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(404, 'Пользователь не найден')
    if user.id == admin.id and (values.is_active is False or (values.role is not None and values.role != UserRole.ADMIN)):
        raise HTTPException(400, 'Нельзя отключить или понизить собственную учётную запись администратора')
    for key, value in values.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    if values.is_active is False:
        await db.execute(update(AuthSession).where(AuthSession.user_id == user.id).values(revoked_at=datetime.now(timezone.utc)))
    await db.commit()
    return user
