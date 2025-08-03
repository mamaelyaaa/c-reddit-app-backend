from fastapi import APIRouter, Depends

from api.auth import http_bearer, ActiveUserDep
from api.posts.schemas import PostSummarySchema
from api.search.service import SearchServiceDep
from api.users.schemas import UserSummaryReadSchema
from core.dependencies import PaginationDep, FiltersDep
from schemas import SearchResponseSchema, SearchResponseSchemaWithFilters

router = APIRouter(
    prefix="/search", tags=["Поиск"], dependencies=[Depends(http_bearer)]
)


@router.get("/users", response_model=SearchResponseSchemaWithFilters[UserSummaryReadSchema])
async def search_users(
    active_user: ActiveUserDep,
    search_service: SearchServiceDep,
    pagination: PaginationDep,
    filters: FiltersDep,
):
    users = await search_service.search_users(
        pagination=pagination,
        filters=filters,
    )
    return users

    # @router.get("/posts", response_model=SearchResponseSchemaWithFilters[PostSummarySchema])
    # async def search_posts(
    #     active_user: ActiveUserDep,
    #     search_service: SearchServiceDep,
    #     pagination: PaginationDep,
    #     filters: FiltersDep,
    # ):
    #     posts = await search_service.search_posts(
    #         pagination=pagination,
    #         filters=filters,
    #     )
    #     return posts
