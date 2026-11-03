# EMBICO Platform

Платформа для клиники ЭКО (репродуктивная медицина).

## 🚀 Быстрый старт

### 1. Установка зависимостей

```bash
# Активируйте виртуальное окружение (если ещё не активировано)
source .venv/bin/activate  # Linux/macOS
# или
.venv\Scripts\activate  # Windows

# Установите зависимости Python
cd backend
pip install -r requirements.txt
```

### 2. Настройка переменных окружения

Файл `.env` уже создан на основе `.env.example`. Проверьте его:

```bash
cat backend/.env
```

**Важно:** Замените `SECRET_KEY` на случайную строку (минимум 32 символа) для production!

### 3. Запуск базы данных (PostgreSQL)

```bash
# Из корневой директории проекта
docker-compose up -d
```

Это запустит:
- **PostgreSQL** на порту `5432`
- **pgAdmin** на порту `5050` (http://localhost:5050)

Данные для входа в pgAdmin:
- Email: `admin@embico.kz`
- Пароль: `admin123`

### 4. Применение миграций

```bash
cd backend

# Применить миграции к БД
alembic upgrade head
```

### 5. Генерация синтетических данных

```bash
# Заполнить БД тестовыми данными
python -m scripts.seed_data
```

Это создаст:
- 5 пользователей (врачи и эмбриологи)
- 20 пациенток
- ~40 циклов ЭКО

**Тестовые учётные записи:**
- Email: `user1@embico.kz` ... `user5@embico.kz`
- Пароль: `password123`

### 6. Запуск сервера

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API Документация

После запуска сервера документация доступна по адресам:

- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc
- **Health check:** http://localhost:8000/health

## 🗂 Структура проекта

```
embico-platform/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   └── api.py           # Главный роутер API
│   │   │   └── endpoints/
│   │   │       └── patients.py      # CRUD endpoints для пациенток
│   │   ├── core/
│   │   │   ├── config.py            # Настройки приложения
│   │   │   └── security.py          # JWT, хеширование
│   │   ├── crud/
│   │   │   └── patient.py           # CRUD функции
│   │   ├── db/
│   │   │   └── database.py          # Подключение к БД
│   │   ├── models/
│   │   │   ├── base.py              # Миксины (timestamps, soft delete)
│   │   │   ├── enums.py             # Enum типы
│   │   │   ├── user.py              # Модель User
│   │   │   ├── patient.py           # Модель Patient
│   │   │   └── cycle.py             # Модель Cycle
│   │   ├── schemas/
│   │   │   └── patient.py           # Pydantic схемы
│   │   └── main.py                  # FastAPI приложение
│   ├── alembic/                     # Миграции БД
│   ├── scripts/
│   │   └── seed_data.py             # Генерация синтетических данных
│   ├── tests/                       # Тесты
│   ├── .env                         # Переменные окружения
│   ├── .env.example                 # Пример настроек
│   ├── alembic.ini                  # Конфигурация Alembic
│   └── requirements.txt             # Зависимости Python
├── docker-compose.yml               # PostgreSQL + pgAdmin
├── CLAUDE.md                        # Контекст проекта
└── README.md                        # Эта инструкция
```

## 🔧 Полезные команды

### Работа с миграциями

```bash
# Создать новую миграцию (автогенерация)
alembic revision --autogenerate -m "описание изменений"

# Применить все миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Посмотреть текущую версию БД
alembic current

# Посмотреть историю миграций
alembic history
```

### Работа с Docker

```bash
# Запустить контейнеры
docker-compose up -d

# Остановить контейнеры
docker-compose down

# Посмотреть логи
docker-compose logs -f postgres

# Полная очистка (удалить контейнеры и volumes)
docker-compose down -v
```

### Тестирование API

```bash
# Получить список пациенток
curl http://localhost:8000/api/v1/patients/

# Создать новую пациентку
curl -X POST http://localhost:8000/api/v1/patients/ \
  -H "Content-Type: application/json" \
  -d '{
    "medical_record_number": "MRN99999",
    "date_of_birth": "1990-01-15",
    "blood_type": "A+",
    "height": 165,
    "weight": 60,
    "amh_level": 3.5
  }'
```

## 📊 Реализованные модули

### ✅ Базовая инфраструктура
- FastAPI приложение
- PostgreSQL в Docker
- SQLAlchemy 2.0 (async)
- Alembic миграции
- Pydantic валидация
- CORS настройки

### ✅ Модели данных
- **User** — пользователи (репродуктолог, эмбриолог)
- **Patient** — пациентки (обезличенные данные)
- **Cycle** — циклы ЭКО

### ✅ API Endpoints
- `GET /api/v1/patients/` — список пациенток
- `GET /api/v1/patients/{id}` — получить пациентку
- `POST /api/v1/patients/` — создать пациентку
- `PUT /api/v1/patients/{id}` — обновить данные
- `DELETE /api/v1/patients/{id}` — удалить (soft delete)

## 🔜 Следующие шаги

1. Добавить JWT авторизацию
2. Реализовать модули:
   - Ооциты
   - Спермограмма
   - Стимуляция
   - Time-lapse
   - Переносы и исходы
3. Добавить тесты (pytest)
4. Создать frontend (React + TypeScript)

## 📝 Технологии

- **Backend:** FastAPI, SQLAlchemy 2.0, PostgreSQL, Alembic
- **Validation:** Pydantic
- **Security:** JWT, bcrypt
- **Dev tools:** Faker, Ruff, pytest
- **Infrastructure:** Docker, docker-compose

---

**Контекст проекта:** См. [CLAUDE.md](CLAUDE.md)
