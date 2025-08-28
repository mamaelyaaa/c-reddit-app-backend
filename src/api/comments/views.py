from fastapi import APIRouter, Depends, status

from api.auth import ActiveUserDep, http_bearer
from core.dependencies import PaginationDep
from schemas import BaseResponseIdSchema, SearchResponseSchema
from .schemas import CommentReadSchema, CommentCreateSchema
from .service import CommentServiceDep

router = APIRouter(
    prefix="/posts",
    tags=["Комментарии"],
    dependencies=[Depends(http_bearer)],
)


@router.post("/{post_id}/comments", response_model=BaseResponseIdSchema)
async def create_comment_for_post(
    active_user: ActiveUserDep,
    comm_service: CommentServiceDep,
    comment: CommentCreateSchema,
    post_id: int,
):
    """Создает комментарий под постом"""

    comment_id = await comm_service.create_comment(
        user_id=active_user.id,
        post_id=post_id,
        content=comment.content,
    )
    return comment_id


# @router.post("/{post_id}/comments/{comment_id}", response_model=BaseResponseIdSchema)
# async def create_comment_for_comment(
#     active_user: ActiveUserDep,
#     comm_service: CommentServiceDep,
#     comment: CommentCreateSchema,
#     post_id: int,
#     comment_id: int
# ):
#     """Создает комментарий под комментарием"""
#
#     return comment_id


@router.delete("/{post_id}/comments", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post_comment(
    active_user: ActiveUserDep,
    comm_service: CommentServiceDep,
    post_id: int,
):
    """
    Удаляет комментарий под постом
    TODO Не проверялось
    """

    await comm_service.delete_user_comment(
        user_id=active_user.id,
        post_id=post_id,
    )
    return


@router.get(
    "/{post_id}/comments", response_model=SearchResponseSchema[CommentReadSchema]
)
async def get_all_post_comments(
    active_user: ActiveUserDep,
    comm_service: CommentServiceDep,
    pagination: PaginationDep,
    post_id: int,
):
    """Вывод комментариев под постом с пагинацией"""

    comments = await comm_service.get_all_post_comments(post_id, pagination)
    return comments


@router.get("/{post_id}/comments/{comment_id}", response_model=CommentReadSchema)
async def get_post_comment(
    active_user: ActiveUserDep,
    comm_service: CommentServiceDep,
    post_id: int,
    comment_id: int,
):
    """Вывод информации о конкретном комментарии под постом"""

    comment = await comm_service.get_user_post_comment(post_id, comment_id)
    return comment
