import logging
from typing import Protocol, Annotated

from fastapi import Depends
from sqlalchemy import delete

from core.dependencies import SessionDep
from repository import RepositoryProtocol, SQLAlchemyRepository
from .models import UserSession

logger = logging.getLogger(__name__)


class UserSessionRepositoryProtocol(RepositoryProtocol[UserSession], Protocol):

    async def delete_all(self, user_id: int) -> None:
        pass


class UserSessionRepositoryImpl(SQLAlchemyRepository):
    model = UserSession

    async def delete_all(self, user_id: int) -> None:
        logger.debug("Удаляем активные сессии пользователя #%d ...", user_id)
        stmt = delete(self.model).filter(self.model.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return


def get_user_session_repository(session: SessionDep) -> UserSessionRepositoryProtocol:
    return UserSessionRepositoryImpl(session)


UserSessionRepositoryDep = Annotated[
    UserSessionRepositoryProtocol, Depends(get_user_session_repository)
]
