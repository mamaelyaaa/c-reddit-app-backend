import logging
import uuid
from datetime import datetime
from typing import Protocol, Annotated

from authx import TokenPayload, RequestToken
from authx.exceptions import MissingTokenError, JWTDecodeError, AccessTokenRequiredError
from fastapi import Depends, Request, Response

from api.users.exceptions import UserNotFoundException, UserAlreadyExists
from api.users.repository import (
    UserRepositoryDep,
    UserRepositoryProtocol,
)
from api.users.schemas import (
    UserReadSchema,
    UserRegisterSchema,
    UserLoginSchema,
    UserUpdateSchema,
    UserUpdatePartialSchema,
)
from core import settings
from core.exceptions import (
    ForbiddenException,
    NotAuthorizedException,
    BadRequestException,
)
from schemas import BaseResponseIdSchema
from utils.security import verify_passwords, hash_password
from .exceptions import (
    WrongPasswordException,
    ActiveSessionNotFoundException,
    ActiveUserRequiredException,
    SuperuserRequiredException,
)
from .repository import (
    UserSessionRepositoryProtocol,
    UserSessionRepositoryDep,
)
from .schemas import BearerResponseSchema
from .security import security

logger = logging.getLogger(__name__)


# TODO 1. Исправить ошибку при /login когда почта не подходит, или когда юзернейм не подходит


class AuthServiceProtocol(Protocol):

    async def register_user(
        self, user_data: UserRegisterSchema
    ) -> BaseResponseIdSchema:
        """Регистрация пользователя в системе"""
        pass

    async def login_user(
        self, user_data: UserLoginSchema, response: Response
    ) -> BearerResponseSchema:
        """Аутентификация пользователя в системе"""
        pass

    async def logout_user(self, request: Request) -> None:
        """Выход из сессии пользователя"""
        pass

    async def refresh_token(self, request: Request) -> BearerResponseSchema:
        """Обновление неактивного токена доступа через токен обновления"""
        pass

    async def revoke_sessions(self, request: Request) -> None:
        """Удаление всех активных сессий текущего пользователя"""
        pass

    async def get_current_user(self, request: Request) -> UserReadSchema:
        """Получение текущего пользователя"""
        pass

    async def get_active_user(self, request: Request) -> UserReadSchema:
        """Получение текущего пользователя (со статусом 'активен')"""
        pass

    async def get_superuser(self, request: Request) -> UserReadSchema:
        """Получение текущего пользователя (со статусом 'супер юзер')"""
        pass

    async def update_user(
        self,
        update_user_data: UserUpdateSchema | UserUpdatePartialSchema,
        user_id: int,
        partial: bool,
    ) -> UserReadSchema:
        """Частичное и полное обновление пользователя"""
        pass


class AuthService:

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        user_session_repo: UserSessionRepositoryProtocol,
    ):
        self.user_repo = user_repo
        self.user_session_repo = user_session_repo

    async def register_user(
        self, user_data: UserRegisterSchema
    ) -> BaseResponseIdSchema:
        logger.info("Регистрируем пользователя '%s'", user_data.username)

        exists_user = await self.user_repo.check_users_exists(
            username=user_data.username, email=str(user_data.email)
        )
        if exists_user:
            logger.error(UserAlreadyExists.message)
            raise UserAlreadyExists

        data = UserRegisterSchema(
            username=user_data.username,
            email=user_data.email,
            password=await hash_password(user_data.password),
            is_superuser=user_data.is_superuser,
        )

        user_id = await self.user_repo.add_user(user_data=data)
        logger.info(f"Пользователь '%s' успешно зарегистрирован!", data.username)
        return BaseResponseIdSchema(id=user_id)

    async def login_user(
        self, user_data: UserLoginSchema, response: Response
    ) -> BearerResponseSchema:
        logger.info("Пользователь '%s' пытается войти в систему", user_data.username)

        user = await self.user_repo.get_user(email=user_data.email)
        if not user:
            logger.error(UserNotFoundException.message)
            raise UserNotFoundException

        logger.debug("Проверяем схожесть пароля ...")

        if not await verify_passwords(
            password=user_data.password,
            hash_pwd=user.password,
        ):
            logger.error(WrongPasswordException.message)
            raise WrongPasswordException

        logger.info("Создаем токены доступа и обновления")

        session_id = str(uuid.uuid4())

        access_token = security.create_access_token(
            uid=str(user.id),
            expiry=settings.jwt.access_expires,
            data={"session_id": session_id},
        )
        refresh_token = security.create_refresh_token(
            uid=str(user.id),
            expiry=settings.jwt.refresh_expires,
            data={"session_id": session_id},
        )
        security.set_refresh_cookies(
            token=refresh_token,
            response=response,
            max_age=settings.jwt.cookie_max_age,
        )

        # Проверяем количество активных сессий пользователя
        # Если сессий больше 3 -> выводим предупреждение
        # sessions = await self.user_session_repo.get_sessions(user_id=user.id)
        # if len(sessions) > 3:
        #     logger.error(TooMuchActiveSessionsException.message)
        #     raise TooMuchActiveSessionsException

        # Создаем новую сессию для пользователя
        await self.user_session_repo.create_session(
            user_id=user.id,
            session_id=session_id,
            refresh_token=refresh_token,
            expired_at=datetime.now() + settings.jwt.refresh_expires,
        )
        logger.info(f"Пользователь '%s' успешно аутентифицировался!", user.username)
        return BearerResponseSchema(access_token=access_token)

    async def logout_user(self, request: Request) -> None:
        token = await self.get_access_token_from_headers(request)

        logger.info("Ищем текущую сессию пользователя #%d", token.sub)
        session = await self.user_session_repo.get_session(
            session_id=token.model_dump()["session_id"]
        )
        if not session:
            logger.error(ActiveSessionNotFoundException.message)
            raise ActiveSessionNotFoundException

        await self.user_session_repo.delete_session(session)
        logger.info(f"Пользователь #%d вышел из системы", int(token.sub))
        return

    async def refresh_token(self, request: Request) -> BearerResponseSchema:
        # Приходит неактуальный токен
        token = await self.get_access_token_from_headers(request, validate=False)

        # Достаем из токена id сессии
        try:
            verf_token = token.verify(
                key=settings.jwt.secret_key,
                algorithms=settings.jwt.algorithm,
                verify_jwt=False,
                verify_csrf=False,
            )

            # Получаем текущую сессию
            session = await self.user_session_repo.get_session(
                session_id=verf_token.model_dump()["session_id"]
            )
            if not session:
                logger.error(ActiveSessionNotFoundException.message)
                raise ActiveSessionNotFoundException

            # Создаем новый токен доступа с этой же сессией
            new_access = security.create_access_token(
                uid=str(session.user_id),
                expiry=settings.jwt.access_expires,
                data={"session_id": verf_token.model_dump()["session_id"]},
            )
            return BearerResponseSchema(access_token=new_access)

        except JWTDecodeError:
            logger.error("Невалидный токен для расшифровки")
            raise NotAuthorizedException("Невалидный токен для расшифровки")

    async def revoke_sessions(self, request: Request) -> None:
        # Приходит верифицированный токен
        token = await self.get_access_token_from_headers(request)

        sessions = await self.user_session_repo.get_sessions(user_id=int(token.sub))
        if not sessions:
            logger.error("Нет активных сессий")
            raise BadRequestException("Нет активных сессий")

        # Находим все активные сессии пользователя и удаляем
        await self.user_session_repo.delete_sessions(user_id=int(token.sub))
        return

    async def get_current_user(self, request: Request) -> UserReadSchema:
        token = await self.get_access_token_from_headers(request)
        current_user = await self.user_repo.get_user(id=int(token.sub))
        return UserReadSchema.model_validate(current_user)

    async def get_active_user(self, request: Request) -> UserReadSchema:
        current_user = await self.get_current_user(request)
        if not current_user.is_active:
            logger.error(ActiveUserRequiredException.message)
            raise ActiveUserRequiredException
        return current_user

    async def get_superuser(self, request: Request) -> UserReadSchema:
        active_user = await self.get_active_user(request)
        if not active_user.is_superuser:
            logger.error(SuperuserRequiredException.message)
            raise SuperuserRequiredException
        return active_user

    async def update_user(
        self,
        update_user_data: UserUpdateSchema | UserUpdatePartialSchema,
        user_id: int,
        partial: bool,
    ) -> UserReadSchema:

        user = await self.user_repo.get_user(id=user_id)
        if not user:
            raise UserNotFoundException

        # Проверяем существование обновляемых полей
        exists_user = await self.user_repo.check_users_exists(
            username=update_user_data.username, email=str(update_user_data.email)
        )
        if exists_user:
            logger.warning(UserAlreadyExists.message)
            raise UserAlreadyExists

        updated_user = await self.user_repo.update_user(
            user=user,
            update_user_data=update_user_data,
            partial=partial,
        )
        logger.info(f"Пользователь {user} успешно обновлен!")

        return UserReadSchema.model_validate(updated_user)

    @staticmethod
    async def get_access_token_from_headers(
        request: Request, validate: bool = True
    ) -> TokenPayload | RequestToken:
        try:
            token = await security.get_access_token_from_request(
                request, locations=["headers"]
            )
            if validate:
                payload = security.verify_token(token, verify_csrf=False)
                return payload
            return token

        except MissingTokenError:
            logger.error("Отсутствует токен доступа в запросе к платформе")
            raise ForbiddenException("Отсутствует токен доступа в запросе к платформе")

        except JWTDecodeError:
            logger.error("Невалидный токен в запросе")
            raise NotAuthorizedException("Невалидный токен в запросе")

        except AccessTokenRequiredError:
            logger.error("Некорректный тип токена")
            raise NotAuthorizedException("Некорректный тип токена")

    @staticmethod
    async def get_refresh_token_from_cookies(
        request: Request, validate: bool = True
    ) -> TokenPayload | RequestToken:
        try:
            token = await security.get_refresh_token_from_request(
                request, locations=["cookies"]
            )
            if validate:
                payload = security.verify_token(token, verify_csrf=False)
                return payload
            return token

        except MissingTokenError:
            logger.error("Отсутствует токен доступа в запросе к платформе")
            raise ForbiddenException("Отсутствует токен доступа в запросе к платформе")

        except JWTDecodeError:
            logger.error("Невалидный токен в запросе")
            raise NotAuthorizedException("Невалидный токен в запросе")

        except AccessTokenRequiredError:
            logger.error("Некорректный тип токена")
            raise NotAuthorizedException("Некорректный тип токена")


async def get_auth_service(
    user_repo: UserRepositoryDep,
    user_session_repo: UserSessionRepositoryDep,
) -> AuthServiceProtocol:
    return AuthService(user_repo, user_session_repo)


AuthServiceDep = Annotated[AuthServiceProtocol, Depends(get_auth_service)]
