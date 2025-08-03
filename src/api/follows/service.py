import logging
from typing import Protocol, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.users.exceptions import UserNotFoundException
from api.users.repository import UserRepositoryProtocol, UserRepositoryDep
from core.dependencies import SessionDep
from .exceptions import FollowAlreadyExists, SelfFollowError, FollowNotFound
from .repository import FollowsRepositoryProtocol, FollowsRepositoryDep

logger = logging.getLogger(__name__)


class FollowsServiceProtocol(Protocol):

    async def subscribe_user(self, cur_user_id: int, target_id: int) -> int:
        pass

    async def unsubscribe_user(self, cur_user_id: int, target_id: int) -> None:
        pass


class FollowsService:

    def __init__(
        self,
        session: AsyncSession,
        follows_repo: FollowsRepositoryProtocol,
        user_repo: UserRepositoryProtocol,
    ):
        self.session = session
        self.follows_repo = follows_repo
        self.user_repo = user_repo

    async def subscribe_user(self, cur_user_id: int, target_id: int) -> int:
        if cur_user_id == target_id:
            logger.warning(SelfFollowError.message)
            raise SelfFollowError

        target_user = await self.user_repo.get_user(id=target_id)
        if not target_user:
            logger.warning(UserNotFoundException.message)
            raise UserNotFoundException

        exists_follow = await self.follows_repo.get_subscription(
            follower_id=cur_user_id, followee_id=target_id
        )
        if exists_follow:
            logger.error(FollowAlreadyExists.message)
            raise FollowAlreadyExists

        follow_id = await self.follows_repo.create_subscription(
            follower_id=cur_user_id, followee_id=target_id
        )
        logger.info(
            f"Пользователь {cur_user_id = } успешно подписался на {target_id = }!"
        )
        return follow_id

    async def unsubscribe_user(self, cur_user_id: int, target_id: int) -> None:
        follow = await self.follows_repo.get_subscription(
            follower_id=cur_user_id, followee_id=target_id
        )
        if not follow:
            logger.warning(FollowNotFound.message)
            raise FollowNotFound

        await self.follows_repo.delete_subscription(follow)
        logger.info(
            f"Пользователь {follow.follower_id = } успешно отписался от {follow.followee_id = }"
        )
        return


async def get_follows_service(
    session: SessionDep,
    follows_repo: FollowsRepositoryDep,
    user_repo: UserRepositoryDep,
) -> FollowsServiceProtocol:
    return FollowsService(session, follows_repo, user_repo)


FollowsServiceDep = Annotated[FollowsServiceProtocol, Depends(get_follows_service)]
