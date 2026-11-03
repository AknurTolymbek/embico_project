"""
Главный роутер API v1.
Здесь подключаются все endpoints приложения.
"""
from fastapi import APIRouter

from app.api.endpoints import patients

api_router = APIRouter()

# Подключаем роутеры endpoints
api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["patients"],
)

# Здесь будут подключаться другие роутеры:
# api_router.include_router(cycles.router, prefix="/cycles", tags=["cycles"])
# api_router.include_router(oocytes.router, prefix="/oocytes", tags=["oocytes"])
# и т.д.
