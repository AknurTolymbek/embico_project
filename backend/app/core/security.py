"""Password hashing and typed JWT primitives shared by authentication services."""
from datetime import datetime, timedelta, timezone
from uuid import uuid4, UUID

import bcrypt
from jose import jwt, JWTError

from app.core.config import settings


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('ascii')


def verify_password(password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('ascii'))
    except (ValueError, TypeError, UnicodeError):
        return False


def create_token(user_id: int, session_id: str, kind: str, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode({
        'sub': str(user_id), 'sid': session_id, 'type': kind,
        'jti': uuid4().hex, 'iat': now, 'exp': now + lifetime,
        'iss': settings.JWT_ISSUER,
    }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str, kind: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                         issuer=settings.JWT_ISSUER,
                         options={'require_exp': True, 'require_iat': True, 'require_sub': True})
    if payload.get('type') != kind or not payload.get('sid') or not payload.get('jti'):
        raise JWTError('Invalid token type or session')
    try:
        UUID(payload['sid'])
        if int(payload['sub']) <= 0:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as exc:
        raise JWTError('Invalid subject') from exc
    return payload


def create_access_token(subject: int, session_id: str, expires_delta: timedelta | None = None) -> str:
    return create_token(subject, session_id, 'access', expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
