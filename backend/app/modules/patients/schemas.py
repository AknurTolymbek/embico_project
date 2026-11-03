"""
Pydantic схемы для Patient.
Используются для валидации данных в API endpoints.
"""
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field


class PatientBase(BaseModel):
    """Базовая схема с общими полями"""
    medical_record_number: str = Field(..., max_length=50, description="Обезличенный медицинский номер")
    date_of_birth: date = Field(..., description="Дата рождения")
    blood_type: str | None = Field(None, max_length=10, description="Группа крови")
    height: Decimal | None = Field(None, ge=0, le=300, description="Рост в см")
    weight: Decimal | None = Field(None, ge=0, le=500, description="Вес в кг")
    amh_level: Decimal | None = Field(None, ge=0, description="Уровень АМГ в нг/мл")


class PatientCreate(PatientBase):
    """Схема для создания новой пациентки"""
    pass


class PatientUpdate(BaseModel):
    """Схема для обновления данных пациентки. Все поля опциональны."""
    medical_record_number: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    blood_type: str | None = Field(None, max_length=10)
    height: Decimal | None = Field(None, ge=0, le=300)
    weight: Decimal | None = Field(None, ge=0, le=500)
    amh_level: Decimal | None = Field(None, ge=0)


class PatientInDB(PatientBase):
    """Схема для данных из БД (включает служебные поля)"""
    id: int
    is_deleted: bool
    deleted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PatientResponse(PatientBase):
    """Схема для ответа API (без is_deleted и deleted_at)"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
