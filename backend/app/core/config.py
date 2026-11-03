"""
Конфигурация приложения EMBICO Platform.
Используем pydantic-settings для загрузки настроек из .env файла.
"""
from typing import List
from pydantic import AnyHttpUrl, EmailStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения"""

    # Application
    APP_NAME: str = "EMBICO Platform"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # Database
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str | None, info) -> str:
        """Собираем DATABASE_URL из отдельных параметров, если он не задан"""
        if v is not None:
            return v

        values = info.data
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] | str = []

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str] | str:
        """Парсим CORS origins из строки JSON или списка"""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # First superuser (для инициализации)
    FIRST_SUPERUSER_EMAIL: EmailStr | None = None
    FIRST_SUPERUSER_PASSWORD: str | None = None
    FIRST_SUPERUSER_ROLE: str = "reproductologist"

    # ML-модели (оценка бластоцисты по фото и time-lapse морфокинетика)
    ML_ENABLED: bool = True
    # Папка с весами: gardner_strict_fold*.pt, cnn_convnext_best.pt, hmm_logA.npy и т.д.
    ML_MODELS_DIR: str = "../ml-model/weights"
    ML_DEVICE: str = "cpu"  # "cpu" или "cuda"
    # Ограничения на загрузку файлов
    ML_MAX_IMAGE_MB: int = 20
    ML_MAX_TIMELAPSE_FRAMES: int = 1000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


# Создаём экземпляр настроек
settings = Settings()
