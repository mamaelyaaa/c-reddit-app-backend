import logging
from typing import (
    Protocol,
    Optional,
    Sequence,
    Annotated,
)

from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from core.dependencies import SessionDep
from .models import Comment

logger = logging.getLogger(__name__)


class CommentRepositoryProtocol(Protocol):

    async def create(self, user_id: int, post_id: int, content: str) -> int:
        pass

    async def read_one(self, *args, **filter_by) -> Optional[Comment]:
        pass

    async def read_all(
        self, limit: int, offset: int, *args, **filter_by
    ) -> Sequence[Comment]:
        pass

    async def count(self, post_id: int) -> int:
        pass

    async def update(self, comment: Comment, upd_comm: str) -> Comment:
        pass

    async def delete(self, comment: Comment) -> None:
        pass


class CommentRepositoryImpl:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, user_id: int, post_id: int, content: str) -> int:
        logger.debug(
            "Пользователь #%d создает комментарий под постом #%d ...", user_id, post_id
        )
        comm = Comment(
            user_id=user_id,
            post_id=post_id,
            content=content,
        )
        self.session.add(comm)
        await self.session.commit()
        logger.debug("Комментарий #%d под постом #%d успешно создан", comm.id, post_id)
        return comm.id

    async def read_one(self, *args, **filter_by) -> Optional[Comment]:
        logger.debug(f"Ищем один комментарий под постом с фильтрами {filter_by} ...")
        query = (
            select(Comment).options(joinedload(Comment.author)).filter_by(**filter_by)
        )
        comm = await self.session.execute(query)
        return comm.scalar_one_or_none()

    async def read_all(
        self, limit: int, offset: int, *args, **filter_by
    ) -> Sequence[Comment]:
        logger.debug(f"Ищем комментарии под постом с фильтрами {filter_by} ...")
        query = (
            select(Comment)
            .options(joinedload(Comment.author))
            .filter_by(**filter_by)
            .limit(limit)
            .offset(offset)
        )
        comms = await self.session.scalars(query)
        return comms.all()

    async def count(self, post_id: int) -> int:
        logger.debug(f"Считаем количество комментариев под постом #%d ...", post_id)
        query = select(func.count(Comment.id)).filter(Comment.post_id == post_id)
        comm = await self.session.execute(query)
        return comm.scalar_one()

    async def update(self, comment: Comment, upd_comm: str) -> Comment:
        logger.debug(
            f"Обновляем комментарий #%d под постом #%d ...", comment.id, comment.post_id
        )
        comment.content = upd_comm
        await self.session.commit()
        return comment

    async def delete(self, comment: Comment) -> None:
        logger.debug(
            f"Удаляем комментарий #%d под постом #%d ...", comment.id, comment.post_id
        )
        await self.session.delete(comment)
        await self.session.commit()
        return


def get_comment_repository(session: SessionDep) -> CommentRepositoryProtocol:
    return CommentRepositoryImpl(session)


CommentRepositoryDep = Annotated[
    CommentRepositoryProtocol, Depends(get_comment_repository)
]
