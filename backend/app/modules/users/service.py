from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select, or_, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate


async def find_by_login(db: AsyncSession, login: str) -> User | None:
    return (await db.execute(select(User).where(or_(User.username == login.lower().strip(), func.lower(User.email) == login.lower().strip())))).scalars().first()


async def create_user(db: AsyncSession, values: UserCreate) -> User:
    # Keep login lookup unambiguous when existing accounts use email to sign in.
    if await find_by_login(db, values.username) or (values.email and await find_by_login(db, values.email)):
        raise HTTPException(409, 'Логин или email уже используется')
    user = User(username=values.username, first_name=values.first_name, last_name=values.last_name,
                full_name=f'{values.first_name} {values.last_name}', email=values.email,
                hashed_password=await run_in_threadpool(get_password_hash, values.password),
                role=values.role, is_active=True)
    db.add(user)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, 'Логин или email уже используется') from exc
    return user
