from fastapi import status

from core import AppException


class WrongPasswordException(AppException):
    message: str = "Неправильный пароль"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_401_UNAUTHORIZED)


class TooMuchActiveSessionsException(AppException):
    message: str = "Количество активных сессий пользователя превышено"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_409_CONFLICT)


class ActiveSessionNotFoundException(AppException):
    message: str = "Сессия пользователя не найдена или не активна"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class SuperuserRequiredException(AppException):
    message: str = "У вас недостаточно прав доступа к этому ресурсу"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)


class ActiveUserRequiredException(AppException):
    message: str = "Ваш аккаунт деактивирован"

    def __init__(self, message: str = message):
        super().__init__(message, status_code=status.HTTP_403_FORBIDDEN)
