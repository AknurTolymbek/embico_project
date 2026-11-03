"""Composition root: public authentication, protected clinical modules."""
from fastapi import APIRouter, Depends

from app.modules.auth.router import router as auth_router
from app.modules.auth.dependencies import get_current_user
from app.modules.users.router import router as users_router
from app.modules.patients.router import router as patients_router
from app.modules.ml.router import router as ml_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix='/auth', tags=['auth'])
api_router.include_router(users_router, prefix='/users', tags=['users'])
api_router.include_router(patients_router, prefix='/patients', tags=['patients'], dependencies=[Depends(get_current_user)])
api_router.include_router(ml_router, prefix='/ml', tags=['ml'], dependencies=[Depends(get_current_user)])
