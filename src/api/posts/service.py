import logging
from typing import Protocol, Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from core.dependencies import SessionDep
from schemas import PaginationSchema, SearchResponseSchema
from .exceptions import PostNotFoundException, PostAlreadyExist
from .repository import PostRepositoryDep, PostRepositoryProtocol
from .schemas import (
    PostCreateSchema,
    PostReadSchema,
    PostUpdateSchema,
    PostUpdatePartialSchema,
    PostSummarySchema,
)

logger = logging.getLogger(__name__)


class PostServiceProtocol(Protocol):

    async def create_post(self, user_id: int, post_data: PostCreateSchema) -> int:
        pass

    async def get_post_by_id(self, post_id: int) -> PostReadSchema:
        pass

    async def get_current_user_posts(
        self, user_id: int
    ) -> SearchResponseSchema[PostSummarySchema]:
        pass

    async def get_post_by_post_id(self, user_id: int, post_id: int) -> PostReadSchema:
        pass

    async def get_posts(
        self,
        user_id: int,
        pagination: PaginationSchema,
    ) -> SearchResponseSchema[PostSummarySchema]:
        pass

    async def update_post(
        self,
        user_id: int,
        post_id: int,
        post_data: PostUpdateSchema | PostUpdatePartialSchema,
        partial: bool,
    ) -> PostReadSchema:
        pass

    async def delete_post(self, user_id: int, post_id: int) -> None:
        pass


class PostService:
    """Сервис постов авторизованного пользователя"""

    def __init__(self, post_repo: PostRepositoryProtocol):
        self.post_repo = post_repo

    async def create_post(self, user_id: int, post_data: PostCreateSchema) -> int:
        exists_post = await self.post_repo.check_exists(
            user_id=user_id,
            title=post_data.title,
        )
        if exists_post:
            logger.error(f"Пользователь #%d уже имеет пост с таким названием", user_id)
            raise PostAlreadyExist

        post_id = await self.post_repo.create(
            {"user_id": user_id, **post_data.model_dump()}
        )
        logger.info(f"Пост #%d пользователя #%d успешно создан!", post_id, user_id)
        return post_id

    async def get_post_by_post_id(self, user_id: int, post_id: int) -> PostReadSchema:
        post = await self.post_repo.read_one(user_id=user_id, id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException
        logger.info(f"Пользователь #%d открыл пост #%d", user_id, post_id)
        return PostReadSchema.model_validate(post)

    async def get_current_user_posts(
        self, user_id: int, pagination: PaginationSchema
    ) -> SearchResponseSchema[PostSummarySchema]:
        count = await self.post_repo.count(user_id=user_id)
        post = await self.post_repo.read_all(
            user_id=user_id, limit=pagination.limit, offset=pagination.offset
        )
        logger.info(f"Пользователь #%d открыл свои посты", user_id)
        return SearchResponseSchema(
            detail=[PostSummarySchema.model_validate(post) for post in posts],
            pagination=pagination,
            total_found=count,
        )

    async def get_post_by_id(self, post_id: int) -> PostReadSchema:
        post = await self.post_repo.read_one(id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException
        return PostReadSchema.model_validate(post)

    async def get_posts(
        self,
        user_id: int,
        pagination: PaginationSchema,
    ) -> SearchResponseSchema[PostSummarySchema]:

        count = await self.post_repo.count(user_id=user_id)
        posts = await self.post_repo.read_all(
            limit=pagination.limit,
            offset=pagination.page_offset,
            user_id=user_id,
        )
        logger.info(f"Пользователь #%d успешно вывел свои посты", user_id)

        return SearchResponseSchema(
            detail=[PostSummarySchema.model_validate(post) for post in posts],
            pagination=pagination,
            total_found=count,
        )

    async def update_post(
        self,
        user_id: int,
        post_id: int,
        post_data: PostUpdateSchema | PostUpdatePartialSchema,
        partial: bool,
    ) -> PostReadSchema:
        post = await self.post_repo.read_one(user_id=user_id, id=post_id)

        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        if post_data.title:
            exists_post = await self.post_repo.check_exists(
                user_id=user_id, title=post_data.title
            )
            if exists_post:
                logger.error(PostAlreadyExist.message)
                raise PostAlreadyExist

        updated_post = await self.post_repo.update(
            model=post,
            upd=post_data.model_dump(exclude_none=partial, exclude_unset=partial),
        )
        logger.info("Пост #%d успешно обновлен!", post_id)
        return PostReadSchema.model_validate(updated_post)

    async def delete_post(self, user_id: int, post_id: int) -> None:
        post = await self.post_repo.read_one(user_id=user_id, id=post_id)
        if not post:
            logger.error(PostNotFoundException.message)
            raise PostNotFoundException

        await self.post_repo.delete(post)
        logger.info(f"Пост #%d успешно удален!", post.id)
        return


def get_posts_service(post_repo: PostRepositoryDep) -> PostServiceProtocol:
    return PostService(post_repo)


PostServiceDep = Annotated[PostServiceProtocol, Depends(get_posts_service)]
