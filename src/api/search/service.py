from typing import Protocol, Annotated

from fastapi import Depends

from api.posts.repository import PostRepositoryDep, PostRepositoryProtocol
from api.posts.schemas import PostSummarySchema
from api.users.repository import UserRepositoryDep, UserRepositoryProtocol
from api.users.schemas import UserSummaryReadSchema
from schemas import (
    PaginationSchema,
    FiltersSchema,
    SearchResponseSchemaWithFilters,
)


class SearchServiceProtocol(Protocol):

    async def search_users(
        self, filters: FiltersSchema, pagination: PaginationSchema
    ) -> SearchResponseSchemaWithFilters[UserSummaryReadSchema]:
        """Выводит список пользователей (сокращенных) с пагинацией, фильтрами и запросом"""
        pass

    async def search_posts(
        self, filters: FiltersSchema, pagination: PaginationSchema
    ) -> SearchResponseSchemaWithFilters[PostSummarySchema]:
        """Выводит список постов (сокращенных) с пагинацией, фильтрами и запросом"""
        pass


class SearchServiceImpl:

    def __init__(
        self,
        user_repo: UserRepositoryProtocol,
        post_repo: PostRepositoryProtocol,
    ):
        self.user_repo = user_repo
        self.post_repo = post_repo

    async def search_users(
        self, filters: FiltersSchema, pagination: PaginationSchema
    ) -> SearchResponseSchemaWithFilters:

        total_users = await self.user_repo.count(filters.query)
        users = await self.user_repo.search_users(
            limit=pagination.limit,
            offset=pagination.page_offset,
            order_by=filters.order_by,
            q=filters.query,
        )

        return SearchResponseSchemaWithFilters(
            detail=[UserSummaryReadSchema.model_validate(user) for user in users],
            filters=filters,
            pagination=pagination,
            total_found=total_users,
        )

    async def search_posts(
        self, filters: FiltersSchema, pagination: PaginationSchema
    ) -> SearchResponseSchemaWithFilters[PostSummarySchema]:
        raise NotImplemented


def get_search_service(
    user_repo: UserRepositoryDep,
    post_repo: PostRepositoryDep,
) -> SearchServiceProtocol:
    return SearchServiceImpl(user_repo, post_repo)


SearchServiceDep = Annotated[SearchServiceProtocol, Depends(get_search_service)]
