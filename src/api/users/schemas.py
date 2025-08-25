from datetime import datetime
from typing import Optional, Annotated

from pydantic import (
    BaseModel,
    EmailStr,
    ConfigDict,
    AfterValidator,
)

from utils.security import validate_password_complexity


class UserBaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    email: EmailStr
    password: Annotated[str, AfterValidator(validate_password_complexity)]


class UserRegisterSchema(UserBaseSchema):
    is_superuser: bool = False


class UserLoginSchema(UserBaseSchema):
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
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)


class UserUpdateSchema(BaseModel):
    username: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)


class UserUpdatePartialSchema(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    model_config = ConfigDict(from_attributes=True)
