from fastapi import status

from core.exceptions import AppException


class UserNotFoundException(AppException):
    message: str = "Пользователь не найден"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_404_NOT_FOUND)


class UserAlreadyExists(AppException):
    message: str = "Пользователь с такими параметрами уже существует"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_400_BAD_REQUEST)
