import logging
from typing import Protocol, Annotated, Optional, Sequence

from fastapi import Depends
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.dependencies import SessionDep
from core.exceptions import BadValidationException
from repository import SQLAlchemyRepository, RepositoryProtocol
from .models import User
from .schemas import UserRegisterSchema, UserUpdateSchema, UserUpdatePartialSchema

logger = logging.getLogger(__name__)


class UserRepositoryProtocol(Protocol):

    async def add_user(self, user_data: UserRegisterSchema) -> int:
        pass

    async def get_user(self, *args, **kwargs) -> Optional[User]:
        pass

    async def get_users(
        self,
        limit: int,
        offset: int,
        q: Optional[str],
        order_by: str,
    ) -> Sequence[User]:
        pass

    async def count(self, q: Optional[str]) -> int:
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
        logger.debug(f"Ищем пользователя ...")
        query = select(User).filter_by(**kwargs)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_users(
        self,
        limit: int,
        offset: int,
        q: Optional[str],
        order_by: str,
    ) -> Sequence[User]:
        logger.debug(
            f"Ищем %d пользователей по запросу %s, начиная с %d ...", limit, q, offset
        )
        query = select(User)

        if q:
            query = query.where(User.username.ilike(f"%{q}%"))

        query = (
            query.order_by(User.id.asc() if order_by == "asc" else User.id.desc())
            .offset(offset)
            .limit(limit)
        )

        res = await self.session.execute(query)
        return res.scalars().all()

    async def count(self, q: Optional[str]) -> int:
        logger.debug('Ищем количество пользователей подходящих по запросу "%s" ...', q)
        query = select(func.count(User.id))
        if q:
            query = query.filter(User.username.ilike(f"%{q}%"))

        count = await self.session.scalar(query)
        return count

    async def check_users_exists(self, username: str, email: str) -> bool:
        logger.debug(
            f'Проверяем существует ли пользователи с юзернеймом "%s" или с почтой "%s"',
            username,
            email,
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
        logger.debug("Обновляем пользователя #%d ...", user.id)

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


def get_user_repository(session: SessionDep) -> UserRepositoryProtocol:
    return UserRepository(session)


class UserSQLRepositoryProtocol(RepositoryProtocol, Protocol):
    pass


class UserAlchemyRepository(SQLAlchemyRepository):
    model = User


def get_user_sql_repository(session: SessionDep) -> UserSQLRepositoryProtocol:
    return UserAlchemyRepository(session)


UserRepositoryDep = Annotated[UserRepositoryProtocol, Depends(get_user_sql_repository)]


# UserRepositoryDep = Annotated[UserRepositoryProtocol, Depends(get_user_repository)]
