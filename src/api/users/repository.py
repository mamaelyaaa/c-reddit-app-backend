import logging
from typing import Protocol, Annotated, Optional, Sequence

from fastapi import Depends
from sqlalchemy import select, or_

from core.dependencies import SessionDep
from repository import SQLAlchemyRepository, RepositoryProtocol
from .models import User

logger = logging.getLogger(__name__)


class UserRepositoryProtocol(RepositoryProtocol[User], Protocol):

    async def check_union_exists(self, *args, **kwargs) -> bool:
        pass

    async def search_users(
        self,
        limit: int,
        offset: int,
        q: Optional[str],
        order_by: str,
    ) -> Sequence[User]:
        pass


class UserRepositoryImpl(SQLAlchemyRepository):
    model = User

    async def check_union_exists(self, *args, **kwargs) -> bool:
        logger.debug(f"Ищем пользователя подходящие под параметры ...")
        union = or_(getattr(self.model, key) == value for key, value in kwargs.items())
        query = select(self.model).where(union)
        res = await self.session.execute(query)
        return len(res.scalars().all()) > 0

    async def search_users(
        self,
        limit: int,
        offset: int,
        q: Optional[str],
        order_by: str,
    ) -> Sequence[User]:
        logger.debug(
            f"Ищем %d пользователей по запросу %s, начиная с %d ...",
            limit,
            q,
            offset,
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


def get_user_repository(session: SessionDep) -> UserRepositoryProtocol:
    return UserRepositoryImpl(session)


UserRepositoryDep = Annotated[UserRepositoryProtocol, Depends(get_user_repository)]
