from typing import Annotated

from aiobcrypt import hashpw_with_salt, checkpw
from pydantic import AfterValidator

from core.exceptions import BadRequestException


async def hash_password(password: str) -> str:
    return (await hashpw_with_salt(password.encode())).decode()


async def verify_passwords(password: str, hash_pwd: str) -> bool:
    return await checkpw(password.encode(), hash_pwd.encode())


def validate_password_complexity(password: str) -> str:
    if len(password) <= 6:
        raise BadRequestException("Пароль должен содержать не менее 6 символов")
    return password


PasswordStr = Annotated[str, AfterValidator(validate_password_complexity)]
