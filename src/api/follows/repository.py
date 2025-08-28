import logging
from typing import Protocol, Annotated, Optional, Sequence

from fastapi import Depends
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import SessionDep
from repository import RepositoryProtocol, SQLAlchemyRepository
from .models import Follow

logger = logging.getLogger(__name__)


class FollowsRepositoryProtocol(Protocol):

    async def create_subscription(self, follower_id: int, followee_id: int) -> int:
        pass

    async def delete_subscription(self, follow: Follow) -> None:
        pass

    async def get_subscription(
        self, follower_id: int, followee_id: int
    ) -> Optional[Follow]:
        pass

    async def get_subs_ids(self, user_id: int) -> Sequence[int]:
        pass


class FollowsRepository:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subscription(self, follower_id: int, followee_id: int) -> int:
        logger.debug(
            f"Пользователь {follower_id = } подписывается на {followee_id = } ..."
        )
        follow = Follow(follower_id=follower_id, followee_id=followee_id)
        self.session.add(follow)
        await self.session.commit()
        return follow.id

    async def delete_subscription(self, follow: Follow) -> None:
        logger.debug(
            f"Пользователь {follow.follower_id = } отписывается от {follow.followee_id = } ..."
        )
        stmt = delete(Follow).filter_by(
            follower_id=follow.follower_id,
            followee_id=follow.followee_id,
        )
        await self.session.execute(stmt)
        await self.session.commit()
        return

    async def get_subscription(
        self, follower_id: int, followee_id: int
    ) -> Optional[Follow]:
        logger.debug(
            f"Ищем подписку пользователя {follower_id = } на {followee_id = } ..."
        )
        query = select(Follow).filter_by(
            follower_id=follower_id, followee_id=followee_id
        )
        follow = await self.session.scalar(query)
        return follow

    async def get_subs_ids(self, user_id: int) -> Sequence[int]:
        logger.debug(f"Ищем уникальные id подписчиков пользователя {user_id = } ...")
        query = select(Follow.follower_id).filter_by(followee_id=user_id)
        follows = await self.session.scalars(query)
        return follows.all()


class IFollowRepositoryProtocol(RepositoryProtocol[Follow], Protocol):
    async def get_subs_ids(self, user_id: int) -> Sequence[int]:
        pass


class IFollowRepository(SQLAlchemyRepository):
    model = Follow

    async def get_subs_ids(self, user_id: int) -> Sequence[int]:
        logger.debug(f"Ищем уникальные id подписчиков пользователя {user_id = } ...")
        query = select(Follow.follower_id).filter_by(followee_id=user_id)
        follows = await self.session.scalars(query)
        return follows.all()


async def get_follows_repository(session: SessionDep) -> IFollowRepositoryProtocol:
    return IFollowRepository(session)


FollowsRepositoryDep = Annotated[
    IFollowRepositoryProtocol, Depends(get_follows_repository)
]
