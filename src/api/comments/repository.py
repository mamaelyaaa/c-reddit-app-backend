import logging
from typing import (
    Protocol,
    Optional,
    Sequence,
    Annotated,
)

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from core.dependencies import SessionDep
from repository import RepositoryProtocol, SQLAlchemyRepository
from .models import Comment

logger = logging.getLogger(__name__)


class CommentRepositoryProtocol(RepositoryProtocol[Comment], Protocol):
    pass


class CommentRepositoryImpl(SQLAlchemyRepository):
    model = Comment

    async def read_one(self, *args, **filter_by) -> Optional[Comment]:
        logger.debug(f"Ищем один комментарий под постом с фильтрами {filter_by} ...")
        query = (
            select(self.model)
            .options(joinedload(self.model.author))
            .filter_by(**filter_by)
        )
        comm = await self.session.execute(query)
        return comm.scalar_one_or_none()

    async def read_all(
        self, limit: int, offset: int, *args, **filter_by
    ) -> Sequence[Comment]:
        logger.debug(f"Ищем комментарии под постом с фильтрами {filter_by} ...")
        query = (
            select(self.model)
            .options(joinedload(self.model.author))
            .filter_by(**filter_by)
            .limit(limit)
            .offset(offset)
        )
        comms = await self.session.scalars(query)
        return comms.all()


def get_comment_repository(session: SessionDep) -> CommentRepositoryProtocol:
    return CommentRepositoryImpl(session)


CommentRepositoryDep = Annotated[
    CommentRepositoryProtocol, Depends(get_comment_repository)
]
