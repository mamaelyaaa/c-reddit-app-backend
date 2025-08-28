from datetime import datetime
from typing import Optional, Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    AfterValidator,
    SecretStr,
)

from utils.security import validate_password_complexity


class UserBaseSchema(BaseModel):
    """Базовая схема для пользователя"""

    username: str
    email: EmailStr
    password: Annotated[SecretStr, AfterValidator(validate_password_complexity)]

    model_config = ConfigDict(extra="forbid")


class UserRegisterSchema(UserBaseSchema):
    """Схема для регистрации пользователя"""

    is_superuser: bool = False


class UserLoginSchema(UserBaseSchema):
    """Схема для аутентификации пользователя"""

    pass


class UserReadSchema(BaseModel):
    """Схема пользователя со всеми полями"""

    id: int
    username: str
    email: EmailStr
    created_at: datetime
    updated_at: datetime
    is_active: bool
    is_superuser: bool = False

    model_config = ConfigDict(from_attributes=True)


class UserSummaryReadSchema(BaseModel):
    """Краткая схема пользователя"""

    id: int
    username: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    """Схема для обновления пользователя"""

    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserUpdatePartialSchema(BaseModel):
    """Схема для частичного обновления пользователя"""

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    model_config = ConfigDict(from_attributes=True)
