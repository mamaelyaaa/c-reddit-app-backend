import logging
from typing import Protocol, Annotated

from fastapi.params import Depends

from schemas import PaginationSchema, SearchResponseSchema
from .exceptions import UserNotFoundException, UserAlreadyExists
from .models import User
from .repository import UserRepositoryProtocol, UserRepositoryDep
from .schemas import UserReadSchema, UserUpdateSchema, UserUpdatePartialSchema

logger = logging.getLogger(__name__)


class UserServiceProtocol(Protocol):

    async def get_user_by_user_id(self, user_id: int) -> UserReadSchema:
        """Получает информацию о пользователе в системе вместе с сокращенными постами"""
        pass

    async def get_users(
        self, pagination: PaginationSchema
    ) -> SearchResponseSchema[UserReadSchema]:
        """Получает список пользователей с пагинацией без постов"""
        pass

    async def update_user(
        self,
        user_id: int,
        upd_user: UserUpdateSchema | UserUpdatePartialSchema,
        partial: bool,
    ) -> UserReadSchema:
        """Обновляет пользователя"""
        pass


class UserServiceImpl:

    def __init__(self, user_repo: UserRepositoryProtocol):
        self.user_repo = user_repo

    async def _get_user_model_by_id(self, user_id: int) -> User:
        user = await self.user_repo.read_one(id=user_id)
        if not user:
            logger.error(UserNotFoundException.message)
            raise UserNotFoundException
        return user

    async def get_user_by_user_id(self, user_id: int) -> UserReadSchema:
        logger.info("Ищем пользователя #%d", user_id)
        user = await self._get_user_model_by_id(user_id)
        return UserReadSchema.model_validate(user)

    async def get_users(
        self, pagination: PaginationSchema
    ) -> SearchResponseSchema[UserReadSchema]:
        raise NotImplemented

    async def update_user(
        self,
        user_id: int,
        upd_user: UserUpdateSchema | UserUpdatePartialSchema,
        partial: bool,
    ) -> UserReadSchema:
        user = await self._get_user_model_by_id(user_id)

        # Проверяем существование обновляемых полей
        exists_user = await self.user_repo.check_union_exists(
            username=upd_user.username, email=str(upd_user.email)
        )
        if exists_user:
            logger.error(UserAlreadyExists.message)
            raise UserAlreadyExists

        upd_user = await self.user_repo.update(
            user, upd_user.model_dump(exclude_none=partial, exclude_unset=partial)
        )
        return UserReadSchema.model_validate(upd_user)


def get_user_service(user_repo: UserRepositoryDep) -> UserServiceProtocol:
    return UserServiceImpl(user_repo)


UserServiceDep = Annotated[UserServiceProtocol, Depends(get_user_service)]
