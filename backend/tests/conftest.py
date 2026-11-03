"""
Общие настройки тестов.

Settings требует POSTGRES_* и SECRET_KEY — задаём тестовые значения ДО импорта app,
чтобы тесты запускались без .env и без реальной базы.
"""
import os

os.environ.setdefault("POSTGRES_USER", "test")
os.environ.setdefault("POSTGRES_PASSWORD", "test")
os.environ.setdefault("POSTGRES_DB", "test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
