"""
API endpoints для работы с пациентками.
CRUD операции: создание, чтение, обновление, удаление.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients import service as crud_patient
from app.db.database import get_db
from app.modules.patients.schemas import PatientCreate, PatientUpdate, PatientResponse

router = APIRouter()


@router.get("/", response_model=List[PatientResponse])
async def get_patients(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить список всех пациенток.

    - **skip**: Количество записей для пропуска (pagination)
    - **limit**: Максимум записей для возврата (по умолчанию 100)
    """
    patients = await crud_patient.get_patients(db, skip=skip, limit=limit)
    return patients


@router.get("/{patient_id}", response_model=PatientResponse)
async def get_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Получить пациентку по ID.

    - **patient_id**: ID пациентки
    """
    patient = await crud_patient.get_patient(db, patient_id=patient_id)
    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пациентка с ID {patient_id} не найдена"
        )
    return patient


@router.post("/", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    Создать новую пациентку.

    - **medical_record_number**: Обезличенный медицинский номер (уникальный)
    - **date_of_birth**: Дата рождения
    - **blood_type**: Группа крови (опционально)
    - **height**: Рост в см (опционально)
    - **weight**: Вес в кг (опционально)
    - **amh_level**: Уровень АМГ в нг/мл (опционально)
    """
    # Проверяем уникальность медицинского номера
    existing_patient = await crud_patient.get_patient_by_mrn(
        db, mrn=patient.medical_record_number
    )
    if existing_patient:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пациентка с медицинским номером '{patient.medical_record_number}' уже существует"
        )

    new_patient = await crud_patient.create_patient(db, patient=patient)
    return new_patient


@router.put("/{patient_id}", response_model=PatientResponse)
async def update_patient(
    patient_id: int,
    patient_update: PatientUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Обновить данные пациентки.

    - **patient_id**: ID пациентки
    - Все поля опциональны, обновляются только переданные
    """
    # Если обновляется medical_record_number, проверяем уникальность
    if patient_update.medical_record_number:
        existing_patient = await crud_patient.get_patient_by_mrn(
            db, mrn=patient_update.medical_record_number
        )
        if existing_patient and existing_patient.id != patient_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Пациентка с медицинским номером '{patient_update.medical_record_number}' уже существует"
            )

    updated_patient = await crud_patient.update_patient(
        db, patient_id=patient_id, patient_update=patient_update
    )
    if not updated_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пациентка с ID {patient_id} не найдена"
        )
    return updated_patient


@router.delete("/{patient_id}", response_model=PatientResponse)
async def delete_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Удалить пациентку (soft delete - помечается как удалённая, не удаляется физически).

    - **patient_id**: ID пациентки
    """
    deleted_patient = await crud_patient.delete_patient(db, patient_id=patient_id)
    if not deleted_patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пациентка с ID {patient_id} не найдена"
        )
    return deleted_patient
