import logging
from typing import Protocol, Annotated

from fastapi import Depends

from api.follows.repository import FollowsRepositoryProtocol, FollowsRepositoryDep
from schemas import SearchResponseSchema, PaginationSchema, FiltersSchema
from .repository import FeedRepositoryProtocol, FeedRepositoryDep
from .schemas import FeedDetailSchema

logger = logging.getLogger(__name__)


class FeedServiceProtocol(Protocol):

    async def create_event_for_users(
        self,
        author_id: int,
        post_id: int,
    ) -> None:
        """Создаем событие для пользователей (подписчиков)"""
        pass

    async def get_user_events(
        self, user_id: int, pagination: PaginationSchema
    ) -> SearchResponseSchema[FeedDetailSchema]:
        """Получаем автора поста, сам пост, тип поста, пагинацию и общее количество"""
        pass


class FeedService:

    def __init__(
        self,
        feed_repo: FeedRepositoryProtocol,
        follows_repo: FollowsRepositoryProtocol,
    ):
        self.feed_repo = feed_repo
        self.follows_repo = follows_repo

    async def create_event_for_users(
        self,
        author_id: int,
        post_id: int,
    ) -> None:
        # Получаем всех подписчиков пользователя
        followers_ids = await self.follows_repo.get_subs_ids(user_id=author_id)

        if not followers_ids:
            logger.warning(
                "У пользователя #%d нет подписчиков. Событие не будет рассылаться никому",
                author_id,
            )
            return

        # Добавляем пачку событий в базу данных
        await self.feed_repo.create_event_for_users(
            author_id=author_id,
            recipients_ids=list(followers_ids),
            post_id=post_id,
        )

        return

    async def get_user_events(
        self, user_id: int, pagination: PaginationSchema
    ) -> SearchResponseSchema[FeedDetailSchema]:
        # Собираем количество всех новостей
        total_events = await self.feed_repo.get_count_events(user_id)

        # Подтягиваем автора новости и саму новость
        events_with_authors = await self.feed_repo.get_full_events_with_authors(
            user_id=user_id,
            limit=pagination.limit,
            offset=(pagination.page - 1) * pagination.limit,
        )

        return SearchResponseSchema(
            detail=[
                FeedDetailSchema.model_validate(event) for event in events_with_authors
            ],
            total_found=total_events,
            pagination=pagination,
        )


async def get_feed_service(
    feed_repo: FeedRepositoryDep,
    follows_repo: FollowsRepositoryDep,
) -> FeedServiceProtocol:
    return FeedService(feed_repo, follows_repo)


FeedServiceDep = Annotated[FeedServiceProtocol, Depends(get_feed_service)]
