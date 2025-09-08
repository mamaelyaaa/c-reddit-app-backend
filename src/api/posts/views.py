from fastapi import APIRouter, Depends, status
from taskiq import AsyncTaskiqTask

from api.auth import ActiveUserDep, http_bearer
from api.tasks.feed_tasks import create_event_for_users
from core.dependencies import PaginationDep
from schemas import SearchResponseSchema
from .schemas import (
    PostCreateSchema,
    PostReadSchema,
    PostUpdateSchema,
    PostUpdatePartialSchema,
    PostSummarySchema,
)
from .service import PostServiceDep

router = APIRouter(
    prefix="/posts",
    tags=["Посты"],
)


@router.post(
    "", status_code=status.HTTP_201_CREATED, dependencies=[Depends(http_bearer)]
)
async def create_post(
    active_user: ActiveUserDep,
    post_service: PostServiceDep,
    post_data: PostCreateSchema,
):
    """Создание поста авторизованного пользователя"""

    post_id = await post_service.create_post(
        user_id=active_user.id, post_data=post_data
    )

    # Отправляем задачу на создание события в брокер
    task: AsyncTaskiqTask = await create_event_for_users.kiq(
        author_id=active_user.id,
        post_id=post_id,
    )
    return {"post_id": post_id, "task_id": task.task_id}


# @router.get("/{post_id}", response_model=PostReadSchema)
# async def get_post_by_post_id(
#     active_user: ActiveUserDep,
#     post_service: PostServiceDep,
#     post_id: int,
# ):
#     """
#     Получение поста авторизованного пользователя по уникальному id
#     Дополнительно: получение комментариев под постом
#     """
#     post = await post_service.get_post_by_post_id(
#         user_id=active_user.id,
#         post_id=post_id,
#     )
#     return post


@router.get("/{post_id}", response_model=PostReadSchema)
async def get_post_by_post_id(
    post_service: PostServiceDep,
    post_id: int,
):
    """
    Получение поста авторизованного пользователя по уникальному id
    Дополнительно: получение комментариев под постом
    """
    post = await post_service.get_post_by_id(post_id=post_id)
    return post


@router.get("", response_model=SearchResponseSchema[PostSummarySchema], dependencies=[Depends(http_bearer)])
async def get_user_posts(
    active_user: ActiveUserDep,
    post_service: PostServiceDep,
    pagination: PaginationDep,
):
    """Получение постов пользователя с пагинацией"""

    posts = await post_service.get_posts(user_id=active_user.id, pagination=pagination)
    return posts


@router.put(
    "/{post_id}", response_model=PostReadSchema, dependencies=[Depends(http_bearer)]
)
async def update_user_post(
    active_user: ActiveUserDep,
    post_service: PostServiceDep,
    post_data: PostUpdateSchema,
    post_id: int,
):
    """Полное обновление поста авторизованного пользователя"""

    post = await post_service.update_post(
        user_id=active_user.id,
        post_id=post_id,
        post_data=post_data,
        partial=False,
    )
    return post


@router.patch(
    "/{post_id}", response_model=PostReadSchema, dependencies=[Depends(http_bearer)]
)
async def update_user_post_partially(
    active_user: ActiveUserDep,
    post_service: PostServiceDep,
    post_data: PostUpdatePartialSchema,
    post_id: int,
):
    """Частичное обновление поста авторизованного пользователя"""

    post = await post_service.update_post(
        user_id=active_user.id,
        post_id=post_id,
        post_data=post_data,
        partial=True,
    )
    return post


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(http_bearer)],
)
async def delete_user_post(
    active_user: ActiveUserDep,
    post_service: PostServiceDep,
    post_id: int,
):
    """Удаление поста авторизованного пользователя"""

    await post_service.delete_post(user_id=active_user.id, post_id=post_id)
    return
