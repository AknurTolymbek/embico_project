"""
Скрипт для генерации синтетических данных.
Создаёт тестовых пользователей, пациенток и циклы с помощью Faker.

Запуск:
    python -m scripts.seed_data
"""
import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.database import AsyncSessionLocal
from app.models import User, Patient, Cycle
from app.models.enums import UserRole, CycleStatus, CycleStage

fake = Faker(['ru_RU'])  # Используем русскую локаль


async def create_users(db: AsyncSession, count: int = 5) -> list[User]:
    """Создаём тестовых пользователей (врачей и эмбриологов)"""
    print(f"Создание {count} пользователей...")

    users = []
    roles = [UserRole.DOCTOR, UserRole.DOCTOR]

    for i in range(count):
        role = random.choice(roles)
        role_ru = "репродуктолог" if role == UserRole.DOCTOR else "эмбриолог"

        first_name, last_name = fake.first_name(), fake.last_name()
        user = User(
            username=f'user{i+1}',
            first_name=first_name,
            last_name=last_name,
            email=f"user{i+1}@embico.kz",
            hashed_password=get_password_hash("password123"),
            role=role,
            full_name=f"{first_name} {last_name}",
            is_active=True,
        )
        db.add(user)
        users.append(user)
        print(f"  - {user.full_name} ({role_ru}): {user.email}")

    await db.commit()
    print(f"✓ Создано {len(users)} пользователей\n")
    return users


async def create_patients(db: AsyncSession, count: int = 20) -> list[Patient]:
    """Создаём тестовых пациенток"""
    print(f"Создание {count} пациенток...")

    patients = []
    blood_types = ["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", None]

    for i in range(count):
        # Возраст от 25 до 45 лет (типичный для ЭКО)
        age = random.randint(25, 45)
        dob = date.today() - timedelta(days=age * 365 + random.randint(0, 365))

        patient = Patient(
            medical_record_number=f"MRN{10000 + i}",
            date_of_birth=dob,
            blood_type=random.choice(blood_types),
            height=Decimal(str(random.randint(150, 180))),  # см
            weight=Decimal(str(random.randint(45, 90))),    # кг
            amh_level=Decimal(str(round(random.uniform(0.5, 8.0), 2))),  # нг/мл
        )
        db.add(patient)
        patients.append(patient)
        print(f"  - Пациентка {patient.medical_record_number}, возраст {age} лет, АМГ {patient.amh_level}")

    await db.commit()
    print(f"✓ Создано {len(patients)} пациенток\n")
    return patients


async def create_cycles(
    db: AsyncSession,
    patients: list[Patient],
    users: list[User],
    cycles_per_patient: tuple[int, int] = (1, 3)
) -> list[Cycle]:
    """Создаём циклы ЭКО для пациенток"""
    print("Создание циклов ЭКО...")

    doctors = [u for u in users if u.role == UserRole.DOCTOR]
    embryologists = [u for u in users if u.role == UserRole.DOCTOR]

    if not doctors:
        doctors = users  # Если нет репродуктологов, берём любых
    if not embryologists:
        embryologists = users

    cycles = []
    statuses = [CycleStatus.ACTIVE, CycleStatus.COMPLETED, CycleStatus.CANCELLED]
    stages = list(CycleStage)

    for patient in patients:
        # Каждая пациентка может иметь от 1 до 3 циклов
        num_cycles = random.randint(*cycles_per_patient)

        for cycle_num in range(1, num_cycles + 1):
            # Дата начала цикла (за последние 2 года)
            start = date.today() - timedelta(days=random.randint(30, 730))

            status = random.choice(statuses)

            # Если завершён или отменён, то есть дата окончания
            if status in [CycleStatus.COMPLETED, CycleStatus.CANCELLED]:
                end = start + timedelta(days=random.randint(30, 90))
                current_stage = CycleStage.OUTCOME
            else:
                end = None
                current_stage = random.choice(stages)

            cycle = Cycle(
                patient_id=patient.id,
                cycle_number=cycle_num,
                start_date=start,
                end_date=end,
                status=status,
                current_stage=current_stage,
                assigned_doctor_id=random.choice(doctors).id if doctors else None,
                assigned_embryologist_id=random.choice(embryologists).id if embryologists else None,
                is_donor_cycle=random.choice([True, False]) if random.random() < 0.2 else False,
                cancellation_reason="Низкий ответ на стимуляцию" if status == CycleStatus.CANCELLED else None,
                notes=fake.text(max_nb_chars=100) if random.random() < 0.3 else None,
            )
            db.add(cycle)
            cycles.append(cycle)

        print(f"  - Пациентка {patient.medical_record_number}: создано {num_cycles} цикл(ов)")

    await db.commit()
    print(f"✓ Создано {len(cycles)} циклов\n")
    return cycles


async def seed_database():
    """Главная функция для заполнения БД синтетическими данными"""
    print("=" * 60)
    print("ГЕНЕРАЦИЯ СИНТЕТИЧЕСКИХ ДАННЫХ ДЛЯ EMBICO PLATFORM")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        # Проверяем, есть ли уже данные
        result = await db.execute(select(User))
        existing_users = result.scalars().all()

        if existing_users:
            print("⚠️  В БД уже есть пользователи. Очистить БД перед генерацией? (y/N): ", end="")
            # В автоматическом режиме пропускаем
            print("Пропускаем генерацию, данные уже есть.\n")
            return

        # Создаём данные
        users = await create_users(db, count=5)
        patients = await create_patients(db, count=20)
        cycles = await create_cycles(db, patients, users, cycles_per_patient=(1, 3))

        print("=" * 60)
        print("ИТОГО:")
        print(f"  Пользователей: {len(users)}")
        print(f"  Пациенток: {len(patients)}")
        print(f"  Циклов ЭКО: {len(cycles)}")
        print("=" * 60)
        print("✓ Синтетические данные успешно созданы!")
        print()
        print("Тестовые учётные записи:")
        for user in users:
            print(f"  Email: {user.email} | Пароль: password123")


if __name__ == "__main__":
    asyncio.run(seed_database())
