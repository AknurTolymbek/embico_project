from datetime import datetime, timezone
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.database import get_db
from app.core.enums import UserRole
from app.modules.users.models import User
from app.modules.auth.models import AuthSession

bearer = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(401, 'Сессия недействительна. Войдите снова.', headers={'WWW-Authenticate': 'Bearer'})


async def get_current_user(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
                           db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    if not credentials:
        raise unauthorized()
    try:
        payload = decode_token(credentials.credentials, 'access')
    except JWTError as exc:
        raise unauthorized() from exc
    session = await db.get(AuthSession, payload['sid'])
    if not session or session.revoked_at or session.user_id != int(payload['sub']) or session.expires_at <= datetime.now(timezone.utc):
        raise unauthorized()
    user = await db.get(User, session.user_id)
    if not user or not user.is_active:
        raise unauthorized()
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(403, 'Требуется роль администратора')
    return user


def protect_cookie(csrf: Annotated[str | None, Header(alias='X-CSRF-Protection')] = None) -> None:
    # A foreign site cannot attach this header without an approved CORS preflight.
    if csrf != '1':
        raise HTTPException(403, 'Отсутствует заголовок защиты запроса')
