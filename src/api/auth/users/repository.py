import logging
from typing import Protocol, Annotated, Optional

from fastapi import Depends
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.dependencies import SessionDep
from core.exceptions import BadValidationException
from .models import User
from .schemas import UserRegisterSchema, UserUpdateSchema, UserUpdatePartialSchema

logger = logging.getLogger(__name__)


class UserRepositoryProtocol(Protocol):

    async def add_user(self, user_data: UserRegisterSchema) -> int:
        pass

    async def get_user(self, *args, **kwargs) -> Optional[User]:
        pass

    async def check_users_exists(self, username: str, email: str) -> bool:
        pass

    async def update_user(
        self,
        user: User,
        update_user_data: UserUpdateSchema | UserUpdatePartialSchema,
        partial: bool,
    ) -> User:
        pass


class UserRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_user(self, user_data: UserRegisterSchema) -> int:
        logger.debug(f"Создаем пользователя %s ...", user_data.username)
        user = User(**user_data.model_dump())
        self.session.add(user)
        await self.session.commit()
        return user.id

    async def get_user(self, *args, **kwargs) -> Optional[User]:
        logger.debug(f"Ищем пользователя {kwargs} ...")
        query = select(User).filter_by(**kwargs)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def check_users_exists(self, username: str, email: str) -> bool:
        logger.debug(
            f"Проверяем существует ли пользователи с {username = }, {email = }"
        )
        query = select(User).where(or_(User.username == username, User.email == email))
        res = await self.session.scalars(query)
        return len(res.all()) > 0

    async def update_user(
        self,
        user: User,
        update_user_data: UserUpdateSchema | UserUpdatePartialSchema,
        partial: bool,
    ) -> User:
        logger.debug("Обновляем пользователя ...")
        for key, value in update_user_data.model_dump(
            exclude_none=partial,
            exclude_unset=partial,
        ).items():
            if not hasattr(user, key):
                logger.error(f"Некорректное поле для обновления: {key}")
                raise BadValidationException(f"Некорректное поле для обновления: {key}")
            setattr(user, key, value)

        await self.session.commit()
        await self.session.refresh(user)
        return user


async def get_user_repository(session: SessionDep) -> UserRepositoryProtocol:
    return UserRepository(session)


UserRepositoryDep = Annotated[UserRepositoryProtocol, Depends(get_user_repository)]
