import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Protocol, Annotated

from authx import TokenPayload, RequestToken
from authx.exceptions import MissingTokenError, JWTDecodeError, AccessTokenRequiredError
from fastapi import Depends, Request, Response
from taskiq import AsyncTaskiqTask

from api.users.exceptions import UserAlreadyExists, UserNotFoundException
from api.users.repository import (
    UserRepositoryDep,
    UserRepositoryProtocol,
)
from api.users.schemas import (
    UserReadSchema,
    UserRegisterSchema,
    UserLoginSchema,
)
from core import settings
from core.exceptions import (
    ForbiddenException,
    NotAuthorizedException,
    BadRequestException,
)
from schemas import BaseResponseTaskSchema
from utils.security import verify_passwords, hash_password
from .exceptions import (
    WrongPasswordException,
    ActiveSessionNotFoundException,
    ActiveUserRequiredException,
    SuperuserRequiredException,
)
from .repository import (
    UserSessionRepositoryDep,
    UserSessionRepositoryProtocol,
    UserVerifTokenRepositoryProtocol,
    UserVerifTokenRepositoryDep,
)
from .schemas import BearerResponseSchema, UserForgotPwdSchema
from .security import security
from ..mailing.repository import EmailRepositoryProtocol, EmailRepositoryDep

logger = logging.getLogger(__name__)


class AuthServiceProtocol(Protocol):

    async def register_user(
        self, user_data: UserRegisterSchema
    ) -> BaseResponseTaskSchema:
        """Регистрация пользователя в системе"""
        pass

    async def login_user(
        self, user_data: UserLoginSchema, response: Response
    ) -> BearerResponseSchema:
        """Аутентификация пользователя в системе"""
        pass

    async def logout_user(self, request: Request, response: Response) -> None:
        """Выход из сессии пользователя"""
        pass

    async def refresh_token(self, request: Request) -> BearerResponseSchema:
        """Обновление неактивного токена доступа через токен обновления"""
        pass

    async def revoke_sessions(self, request: Request, response: Response) -> None:
        """Удаление всех активных сессий текущего пользователя"""
        pass

    async def forgot_password(self, user_info: UserForgotPwdSchema) -> None:
        """Запрашивает о том, что пользователь забыл пароль"""
        pass

    async def reset_password(self, token: str, user_id: int):
        """Сбрасывает пароль пользователя"""
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


class AuthService:

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        user_session_repo: UserSessionRepositoryProtocol,
        email_repo: EmailRepositoryProtocol,
        user_verif_token_repo: UserVerifTokenRepositoryProtocol,
    ):
        self.user_repo = user_repo
        self.user_session_repo = user_session_repo
        self.email_repo = email_repo
        self.user_verif_token_repo = user_verif_token_repo

    async def register_user(
        self, user_data: UserRegisterSchema
    ) -> BaseResponseTaskSchema:
        logger.debug("Регистрируем пользователя '%s'", user_data.username)
        exists_user = await self.user_repo.check_union_exists(
            username=user_data.username, email=str(user_data.email)
        )
        if exists_user:
            logger.error(UserAlreadyExists.message)
            raise UserAlreadyExists

        data = {
            "username": user_data.username,
            "email": user_data.email,
            "password": await hash_password(user_data.password.get_secret_value()),
            "is_superuser": user_data.is_superuser,
        }
        user_id = await self.user_repo.create(data)
        logger.info(f"Пользователь '%s' успешно зарегистрирован!", data["username"])

        # Отправляем письмо на почту пользователя

        task: AsyncTaskiqTask[None] = await self.email_repo.send_email.kiq(
            recipient=user_data.email,
            subject=f"{user_data.username.capitalize()}, добро пожаловать на нашу платформу!",
            body="Бу",
        )

        return BaseResponseTaskSchema(id=user_id, task_id=task.task_id)

    async def login_user(
        self,
        user_data: UserLoginSchema,
        response: Response,
    ) -> BearerResponseSchema:
        logger.debug("Пользователь '%s' пытается войти в систему", user_data.username)

        user = await self.user_repo.read_one(
            username=user_data.username, email=user_data.email
        )
        if not user:
            logger.error("Неправильная почта или юзернейм")
            raise NotAuthorizedException("Неправильная почта или юзернейм")

        logger.debug("Проверяем схожесть пароля ...")

        if not await verify_passwords(
            password=user_data.password.get_secret_value(),
            hash_pwd=user.password,
        ):
            logger.error(WrongPasswordException.message)
            raise WrongPasswordException

        logger.debug("Создаем новые токены доступа и обновления")

        fingerprint = str(uuid.uuid4())
        access_token = security.create_access_token(
            uid=str(user.id),
            expiry=settings.jwt.access_expires,
            data={"fingerprint": fingerprint},
        )
        refresh_token = security.create_refresh_token(
            uid=str(user.id),
            expiry=settings.jwt.refresh_expires,
            data={"fingerprint": fingerprint},
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
        await self.user_session_repo.create(
            {
                "user_id": user.id,
                "fingerprint": fingerprint,
                "refresh_token": refresh_token,
                "expired_at": datetime.now() + settings.jwt.refresh_expires,
            }
        )
        logger.info(f"Пользователь '%s' успешно аутентифицировался!", user.username)
        return BearerResponseSchema(access_token=access_token)

    async def logout_user(self, request: Request, response: Response) -> None:
        token = await self.get_access_token_from_headers(request)
        logger.debug("Ищем текущую сессию пользователя #%d", int(token.sub))

        session = await self.user_session_repo.read_one(
            fingerprint=token.model_dump()["fingerprint"]
        )
        if not session:
            logger.error(ActiveSessionNotFoundException.message)
            raise ActiveSessionNotFoundException

        await self.user_session_repo.delete(session)
        security.unset_cookies(response)
        logger.info(f"Пользователь #%d вышел из системы", int(token.sub))
        return

    async def refresh_token(self, request: Request) -> BearerResponseSchema:
        # Проверяем токен обновления в куки
        refr_token = await self.get_refresh_token_from_cookies(request)
        new_access = security.create_access_token(
            uid=str(refr_token.sub),
            expiry=settings.jwt.access_expires,
            data={"fingerprint": refr_token.model_dump()["fingerprint"]},
        )
        logger.info("Пользователь #%d обновил токен доступа", int(refr_token.sub))
        return BearerResponseSchema(access_token=new_access)

    async def revoke_sessions(self, request: Request, response: Response) -> None:
        # Приходит верифицированный токен
        token = await self.get_access_token_from_headers(request)
        sessions = await self.user_session_repo.read_all(
            user_id=int(token.sub),
            limit=None,
            offset=None,
        )
        if not sessions:
            logger.error("Нет активных сессий")
            raise BadRequestException("Нет активных сессий")

        # Находим все активные сессии пользователя и удаляем
        await self.user_session_repo.delete_all(user_id=int(token.sub))
        security.unset_cookies(response)
        logger.info("Пользователь #%d вышел со всех активных сессий", int(token.sub))
        return

    async def forgot_password(self, user_info: UserForgotPwdSchema) -> None:
        exists_user = await self.user_repo.read_one(
            username=user_info.username,
            email=user_info.email,
        )
        if not exists_user:
            logger.error(UserNotFoundException.message)
            raise UserNotFoundException

        exists_request = await self.user_verif_token_repo.read_one(
            user_id=exists_user.id
        )
        if exists_request:
            if exists_request.expired_at.astimezone() < datetime.now(tz=timezone.utc):
                logger.info("Повторно отправляем запрос на восстановление")
                await self.user_verif_token_repo.delete(exists_request)
            else:
                logger.error(
                    "Запрос на восстановление пароля уже отправлен. Проверьте свою почту"
                )
                raise BadRequestException(
                    "Запрос на восстановление пароля уже отправлен. Проверьте свою почту"
                )

        unique_token = uuid.uuid4()
        hashed_token = await hash_password(str(unique_token))

        # Сохраняем запись о восстановлении пароля в БД
        await self.user_verif_token_repo.create(
            {
                "user_id": exists_user.id,
                "hashed_token": hashed_token,
                "expired_at": datetime.now() + timedelta(minutes=15),
            }
        )

        # Отправляем на почту письмо с подтверждением операции
        await self.email_repo.send_verification_email.kiq(
            recipient=user_info.email,
            token=unique_token,
            user_id=exists_user.id,
        )
        return

    async def reset_password(self, token: str, user_id: int):
        exists_req = await self.user_verif_token_repo.read_one(user_id=user_id)

        if not (
            exists_req and await verify_passwords(token, str(exists_req.hashed_token))
        ):
            logger.error("Запрос на восстановление не найден")
            raise BadRequestException("Запрос на восстановление не найден")

        logger.info("Запрос на восстановление найден")

        # TODO Реализовать имплементацию отправки формы для обновления пароля

        await self.user_verif_token_repo.delete(exists_req)
        return

    async def get_current_user(self, request: Request) -> UserReadSchema:
        token = await self.get_access_token_from_headers(request)
        logger.info("Пользователь #%d получает информацию о себе", int(token.sub))
        current_user = await self.user_repo.read_one(id=int(token.sub))
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
    async def get_fresh_token_from_headers(
        request: Request, validate: bool = True
    ) -> TokenPayload | RequestToken:
        try:
            token = await security.get_access_token_from_request(
                request, locations=["headers"]
            )
            if validate:
                payload = security.verify_token(
                    token, verify_csrf=False, verify_fresh=True
                )
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
    email_repo: EmailRepositoryDep,
    user_verif_token_repo: UserVerifTokenRepositoryDep,
) -> AuthServiceProtocol:
    return AuthService(user_repo, user_session_repo, email_repo, user_verif_token_repo)


AuthServiceDep = Annotated[AuthServiceProtocol, Depends(get_auth_service)]
