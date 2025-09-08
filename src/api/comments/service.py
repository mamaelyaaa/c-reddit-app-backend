import logging
from typing import Protocol, Annotated

from fastapi import Depends

from api.posts.exceptions import PostNotFoundException
from api.posts.repository import PostRepositoryDep
from core.exceptions import NotFoundException
from schemas import PaginationSchema, BaseResponseIdSchema, SearchResponseSchema
from .models import Comment
from .repository import CommentRepositoryProtocol, CommentRepositoryDep
from .schemas import (
    CommentReadSchema,
    CommentUpdateSchema,
)

logger = logging.getLogger(__name__)


class CommentServiceProtocol(Protocol):

    async def create_comment(
        self, user_id: int, post_id: int, content: str
    ) -> BaseResponseIdSchema:
        pass

    async def get_all_post_comments(
        self, post_id: int, pagination: PaginationSchema
    ) -> SearchResponseSchema[CommentReadSchema]:
        pass

    async def get_user_post_comment(
        self, post_id: int, comment_id: int
    ) -> CommentReadSchema:
        pass

    async def update_user_comment(
        self,
        post_id: int,
        comment_id: int,
        upd_comm: CommentUpdateSchema,
    ) -> CommentReadSchema:
        pass

    async def delete_user_comment(
        self, post_id: int, user_id: int, comment_id: int
    ) -> None:
        pass


class CommentServiceImpl:

    def __init__(
        self,
        comm_repo: CommentRepositoryProtocol,
        post_repo: PostRepositoryDep,
    ):
        self.comm_repo = comm_repo
        self.post_repo = post_repo

    async def _get_base_user_post_comment(
        self, post_id: int, comment_id: int
    ) -> Comment:
        comment = await self.comm_repo.read_one(post_id=post_id, id=comment_id)
        if not comment:
            logger.error("Комментарий не найден")
            raise NotFoundException("Комментарий не найден")
        return comment

    async def create_comment(
        self, user_id: int, post_id: int, content: str
    ) -> BaseResponseIdSchema:
        post = await self.post_repo.read_one(id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        comm_id = await self.comm_repo.create(
            {
                "user_id": user_id,
                "post_id": post_id,
                "content": content,
            }
        )
        await self.post_repo.increment_post_comments(post)

        logger.info("Комментарий #%d под постом #%d успешно создан!", comm_id, post_id)
        return BaseResponseIdSchema(id=comm_id)

    async def get_all_post_comments(
        self, post_id: int, pagination: PaginationSchema
    ) -> SearchResponseSchema[CommentReadSchema]:
        post = await self.post_repo.read_one(id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        total_count = await self.comm_repo.count(post_id=post_id)

        comments = await self.comm_repo.read_all(
            limit=pagination.limit,
            offset=(pagination.page - 1) * pagination.limit,
            post_id=post_id,
        )

        logger.info(
            "Пользователь вывел %d комментариев под постом #%d, начиная с %d",
            pagination.limit,
            post_id,
            (pagination.page - 1) * pagination.limit,
        )

        return SearchResponseSchema(
            detail=[CommentReadSchema.model_validate(comm) for comm in comments],
            pagination=pagination,
            total_found=total_count,
        )

    async def get_user_post_comment(
        self, post_id: int, comment_id: int
    ) -> CommentReadSchema:
        post = await self.post_repo.read_one(id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        comment = await self._get_base_user_post_comment(
            post_id=post_id, comment_id=comment_id
        )
        logger.info(
            "Пользователь открыл комментарий #%d под постом #%d",
            comment.id,
            post_id,
        )
        return CommentReadSchema.model_validate(comment)

    async def update_user_comment(
        self,
        post_id: int,
        comment_id: int,
        upd_comm: CommentUpdateSchema,
    ) -> CommentReadSchema:
        post = await self.post_repo.read_one(id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        comment = await self._get_base_user_post_comment(
            post_id=post_id,
            comment_id=comment_id,
        )
        upd_comment = await self.comm_repo.update(
            model=comment,
            upd={"content": upd_comm.content},
        )
        logger.info(
            "Пользователь обновил комментарий #%d под постом #%d",
            comment.id,
            post_id,
        )
        return CommentReadSchema.model_validate(upd_comment)

    async def delete_user_comment(
        self, post_id: int, user_id: int, comment_id: int
    ) -> None:
        post = await self.post_repo.read_one(id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        comment = await self._get_base_user_post_comment(
            post_id=post_id,
            comment_id=comment_id,
        )
        await self.comm_repo.delete(comment)
        return


async def get_comment_service(
    comm_repo: CommentRepositoryDep,
    post_repo: PostRepositoryDep,
) -> CommentServiceProtocol:
    return CommentServiceImpl(comm_repo, post_repo)


CommentServiceDep = Annotated[CommentServiceProtocol, Depends(get_comment_service)]
