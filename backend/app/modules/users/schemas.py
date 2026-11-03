from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, StringConstraints, field_validator

from app.core.enums import UserRole

Username = Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True, min_length=3, max_length=80, pattern=r'^[a-z0-9_.@+\-]+$')]
Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
Password = Annotated[str, Field(min_length=8, max_length=72)]


class UserCreate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    username: Username
    password: Password
    first_name: Name
    last_name: Name
    email: EmailStr | None = None
    role: UserRole = UserRole.DOCTOR

    @field_validator('password')
    @classmethod
    def password_length(cls, value: str) -> str:
        if len(value.encode('utf-8')) > 72:
            raise ValueError('Пароль должен занимать не более 72 байт UTF-8')
        return value

    @field_validator('email')
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.lower() if value else None


class RegisterRequest(UserCreate):
    role: Literal['doctor'] = 'doctor'


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    first_name: str
    last_name: str
    full_name: str
    email: str | None
    role: UserRole
    is_active: bool


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    first_name: Name | None = None
    last_name: Name | None = None

    @field_validator('first_name', 'last_name')
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError('Имя и фамилия не могут быть null')
        return value


class AdminUserUpdate(BaseModel):
    model_config = ConfigDict(extra='forbid')
    role: UserRole | None = None
    is_active: bool | None = None

    @field_validator('role', 'is_active')
    @classmethod
    def not_null(cls, value):
        if value is None:
            raise ValueError('Поле не может быть null')
        return value
