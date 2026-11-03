"""
CRUD операции для Patient.
Create, Read, Update, Delete (soft delete) функции для работы с пациентками.
"""
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.patients.models import Patient
from app.modules.patients.schemas import PatientCreate, PatientUpdate


async def get_patient(db: AsyncSession, patient_id: int) -> Patient | None:
    """
    Получить пациентку по ID (только не удалённые).

    Args:
        db: Async сессия БД
        patient_id: ID пациентки

    Returns:
        Patient или None если не найдена
    """
    result = await db.execute(
        select(Patient).where(
            Patient.id == patient_id,
            Patient.is_deleted == False  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def get_patient_by_mrn(db: AsyncSession, mrn: str) -> Patient | None:
    """
    Получить пациентку по медицинскому номеру.

    Args:
        db: Async сессия БД
        mrn: Медицинский номер (medical_record_number)

    Returns:
        Patient или None если не найдена
    """
    result = await db.execute(
        select(Patient).where(
            Patient.medical_record_number == mrn,
            Patient.is_deleted == False  # noqa: E712
        )
    )
    return result.scalar_one_or_none()


async def get_patients(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> List[Patient]:
    """
    Получить список пациенток (только не удалённые).

    Args:
        db: Async сессия БД
        skip: Сколько записей пропустить (для пагинации)
        limit: Максимум записей для возврата

    Returns:
        Список пациенток
    """
    result = await db.execute(
        select(Patient)
        .where(Patient.is_deleted == False)  # noqa: E712
        .offset(skip)
        .limit(limit)
        .order_by(Patient.created_at.desc())
    )
    return list(result.scalars().all())


async def create_patient(db: AsyncSession, patient: PatientCreate) -> Patient:
    """
    Создать новую пациентку.

    Args:
        db: Async сессия БД
        patient: Данные для создания пациентки

    Returns:
        Созданная пациентка
    """
    db_patient = Patient(**patient.model_dump())
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    return db_patient


async def update_patient(
    db: AsyncSession,
    patient_id: int,
    patient_update: PatientUpdate,
) -> Patient | None:
    """
    Обновить данные пациентки.

    Args:
        db: Async сессия БД
        patient_id: ID пациентки
        patient_update: Данные для обновления

    Returns:
        Обновлённая пациентка или None если не найдена
    """
    db_patient = await get_patient(db, patient_id)
    if not db_patient:
        return None

    # Обновляем только те поля, которые переданы
    update_data = patient_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_patient, field, value)

    await db.commit()
    await db.refresh(db_patient)
    return db_patient


async def delete_patient(db: AsyncSession, patient_id: int) -> Patient | None:
    """
    Soft delete пациентки (помечаем как удалённую, не удаляем физически).

    Args:
        db: Async сессия БД
        patient_id: ID пациентки

    Returns:
        Удалённая пациентка или None если не найдена
    """
    db_patient = await get_patient(db, patient_id)
    if not db_patient:
        return None

    db_patient.is_deleted = True
    db_patient.deleted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(db_patient)
    return db_patient
