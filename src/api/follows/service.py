import logging
from typing import Protocol, Annotated

from fastapi import Depends

from api.users.exceptions import UserNotFoundException
from api.users.repository import UserRepositoryDep, UserRepositoryProtocol
from .exceptions import FollowAlreadyExists, SelfFollowError, FollowNotFound
from .repository import (
    FollowsRepositoryDep,
    IFollowRepositoryProtocol,
)

logger = logging.getLogger(__name__)


class FollowsServiceProtocol(Protocol):

    async def subscribe_user(self, cur_user_id: int, target_id: int) -> int:
        pass

    async def unsubscribe_user(self, cur_user_id: int, target_id: int) -> None:
        pass


class FollowsService:

    def __init__(
        self,
        follows_repo: IFollowRepositoryProtocol,
        user_repo: UserRepositoryProtocol,
    ):
        self.follows_repo = follows_repo
        self.user_repo = user_repo

    async def subscribe_user(self, cur_user_id: int, target_id: int) -> int:
        if cur_user_id == target_id:
            logger.warning(SelfFollowError.message)
            raise SelfFollowError

        target_user = await self.user_repo.read_one(id=target_id)
        if not target_user:
            logger.warning(UserNotFoundException.message)
            raise UserNotFoundException

        exists_follow = await self.follows_repo.read_one(
            follower_id=cur_user_id, followee_id=target_id
        )
        if exists_follow:
            logger.error(FollowAlreadyExists.message)
            raise FollowAlreadyExists

        follow_id = await self.follows_repo.create(
            {"follower_id": cur_user_id, "followee_id": target_id}
        )
        logger.info(
            f"Пользователь #%d успешно подписался на #%d!", cur_user_id, target_id
        )
        return follow_id

    async def unsubscribe_user(self, cur_user_id: int, target_id: int) -> None:
        follow = await self.follows_repo.read_one(
            follower_id=cur_user_id, followee_id=target_id
        )
        if not follow:
            logger.warning(FollowNotFound.message)
            raise FollowNotFound

        await self.follows_repo.delete(follow)
        logger.info(
            f"Пользователь #%d отписался от пользователя #%d", cur_user_id, target_id
        )
        return


async def get_follows_service(
    follows_repo: FollowsRepositoryDep, user_repo: UserRepositoryDep
) -> FollowsServiceProtocol:
    return FollowsService(follows_repo, user_repo)


FollowsServiceDep = Annotated[FollowsServiceProtocol, Depends(get_follows_service)]
