from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.database import get_db
from app.modules.auth import service
from app.modules.auth.dependencies import get_current_user, protect_cookie
from app.modules.auth.schemas import LoginRequest, TokenResponse
from app.modules.users.models import User
from app.modules.users.schemas import RegisterRequest, UserResponse
from app.modules.users.service import create_user

router = APIRouter()
DB = Annotated[AsyncSession, Depends(get_db)]


def set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(settings.AUTH_COOKIE_NAME, token, httponly=True, secure=settings.AUTH_COOKIE_SECURE,
                        samesite='lax', max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                        path=f'{settings.API_V1_PREFIX}/auth')
    response.headers['Cache-Control'] = 'no-store'


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(settings.AUTH_COOKIE_NAME, path=f'{settings.API_V1_PREFIX}/auth',
                           secure=settings.AUTH_COOKIE_SECURE, httponly=True, samesite='lax')
    response.headers['Cache-Control'] = 'no-store'


@router.post('/register', response_model=TokenResponse, status_code=201, dependencies=[Depends(protect_cookie)])
async def register(values: RegisterRequest, response: Response, db: DB):
    user = await create_user(db, values)
    tokens, refresh = await service.start_session(db, user)
    set_refresh_cookie(response, refresh)
    return tokens


@router.post('/login', response_model=TokenResponse, dependencies=[Depends(protect_cookie)])
async def login(values: LoginRequest, response: Response, db: DB):
    tokens, refresh = await service.login(db, values.username, values.password)
    set_refresh_cookie(response, refresh)
    return tokens


@router.post('/refresh', response_model=TokenResponse, dependencies=[Depends(protect_cookie)])
async def refresh(request: Request, response: Response, db: DB):
    try:
        tokens, refresh_token = await service.refresh_session(db, request.cookies.get(settings.AUTH_COOKIE_NAME))
    except HTTPException as exc:
        failure = JSONResponse(status_code=exc.status_code, content={'detail': exc.detail}, headers=exc.headers)
        clear_refresh_cookie(failure)
        return failure
    set_refresh_cookie(response, refresh_token)
    return tokens


@router.post('/logout', status_code=204, dependencies=[Depends(protect_cookie)])
async def logout(request: Request, db: DB):
    await service.logout(db, request.cookies.get(settings.AUTH_COOKIE_NAME))
    response = Response(status_code=204)
    clear_refresh_cookie(response)
    return response


@router.get('/me', response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]):
    return user
