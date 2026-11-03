"""
Главный роутер API v1.
Здесь подключаются все endpoints приложения.
"""
from fastapi import APIRouter

from app.api.endpoints import ml, patients

api_router = APIRouter()

# Подключаем роутеры endpoints
api_router.include_router(
    patients.router,
    prefix="/patients",
    tags=["patients"],
)
api_router.include_router(
    ml.router,
    prefix="/ml",
    tags=["ml"],
)

# Здесь будут подключаться другие роутеры:
# api_router.include_router(cycles.router, prefix="/cycles", tags=["cycles"])
# api_router.include_router(oocytes.router, prefix="/oocytes", tags=["oocytes"])
# и т.д.
