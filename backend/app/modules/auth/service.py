from datetime import datetime, timedelta, timezone
import hashlib
import hmac
from uuid import uuid4

from fastapi import HTTPException
from fastapi.concurrency import run_in_threadpool
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import create_access_token, create_token, decode_token, get_password_hash, verify_password
from app.modules.auth.dependencies import unauthorized
from app.modules.auth.models import AuthSession
from app.modules.auth.schemas import TokenResponse
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse
from app.modules.users.service import find_by_login

DUMMY_HASH = get_password_hash('not-an-account-password')


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_tokens(user: User, session: AuthSession) -> tuple[TokenResponse, str]:
    lifetime = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh = create_token(user.id, session.id, 'refresh', lifetime)
    session.refresh_hash = token_hash(refresh)
    # Use the actual JWT expiry so database and signed token agree to the second.
    session.expires_at = datetime.fromtimestamp(decode_token(refresh, 'refresh')['exp'], timezone.utc)
    access = create_access_token(user.id, session.id)
    return TokenResponse(access_token=access, expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                         user=UserResponse.model_validate(user)), refresh


async def start_session(db: AsyncSession, user: User) -> tuple[TokenResponse, str]:
    session = AuthSession(id=str(uuid4()), user_id=user.id)
    db.add(session)
    tokens = issue_tokens(user, session)
    await db.commit()
    return tokens


async def login(db: AsyncSession, username: str, password: str) -> tuple[TokenResponse, str]:
    user = await find_by_login(db, username)
    valid = await run_in_threadpool(verify_password, password, user.hashed_password if user else DUMMY_HASH)
    if not user or not valid or not user.is_active:
        raise HTTPException(401, 'Неверный логин или пароль', headers={'WWW-Authenticate': 'Bearer'})
    return await start_session(db, user)


async def refresh_session(db: AsyncSession, refresh: str | None) -> tuple[TokenResponse, str]:
    if not refresh:
        raise unauthorized()
    try:
        payload = decode_token(refresh, 'refresh')
    except JWTError as exc:
        raise unauthorized() from exc
    session = (await db.execute(select(AuthSession).where(AuthSession.id == payload['sid']).with_for_update())).scalar_one_or_none()
    if (not session or session.revoked_at or session.user_id != int(payload['sub'])
            or session.expires_at <= datetime.now(timezone.utc)
            or not hmac.compare_digest(session.refresh_hash, token_hash(refresh))):
        raise unauthorized()
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise unauthorized()
    tokens = issue_tokens(user, session)
    await db.commit()
    return tokens


async def logout(db: AsyncSession, refresh: str | None) -> None:
    if refresh:
        try:
            payload = decode_token(refresh, 'refresh')
        except JWTError:
            return
        session = (await db.execute(select(AuthSession).where(AuthSession.id == payload['sid']).with_for_update())).scalar_one_or_none()
        if session and session.user_id == int(payload['sub']) and hmac.compare_digest(session.refresh_hash, token_hash(refresh)):
            session.revoked_at = datetime.now(timezone.utc)
            await db.commit()
