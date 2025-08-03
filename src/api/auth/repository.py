import logging
from datetime import datetime
from typing import Protocol, Annotated, Optional, Sequence

from fastapi import Depends
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from core.dependencies import SessionDep
from .models import UserSession

logger = logging.getLogger(__name__)


class UserSessionRepositoryProtocol(Protocol):

    async def create_session(
        self, user_id: int, session_id: str, refresh_token: str, expired_at: datetime
    ) -> int:
        pass

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        pass

    async def get_sessions(self, user_id: int) -> Sequence[UserSession]:
        pass

    async def delete_session(self, session: UserSession) -> None:
        pass

    async def delete_sessions(self, user_id: int) -> None:
        pass


class UserSessionRepositoryImpl:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_session(
        self, user_id: int, session_id: str, refresh_token: str, expired_at: datetime
    ) -> int:
        logger.debug("Создаем сессию #%s для пользователя #%d ...", session_id, user_id)
        user_session = UserSession(
            user_id=user_id,
            session_id=session_id,
            refresh_token=refresh_token,
            expired_at=expired_at,
        )
        self.session.add(user_session)
        await self.session.commit()
        return user_session.id

    async def get_session(self, session_id: str) -> Optional[UserSession]:
        logger.debug("Ищем активную сессию #%s ...", session_id)
        query = select(UserSession).filter(UserSession.session_id == session_id)
        res = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def get_sessions(self, user_id: int) -> Sequence[UserSession]:
        logger.debug("Ищем активные сессии пользователя #%d ...", user_id)
        query = select(UserSession).filter_by(user_id=user_id)
        res = await self.session.execute(query)
        return res.scalars().all()

    async def delete_session(self, session: UserSession) -> None:
        logger.debug("Удаляем активную сессию #%s ...", session.session_id)
        await self.session.delete(session)
        await self.session.commit()
        return

    async def delete_sessions(self, user_id: int) -> None:
        logger.debug("Удаляем активные сессии пользователя #%d ...", user_id)
        stmt = delete(UserSession).filter(UserSession.user_id == user_id)
        await self.session.execute(stmt)
        await self.session.commit()
        return


def get_user_session_repository(session: SessionDep) -> UserSessionRepositoryProtocol:
    return UserSessionRepositoryImpl(session)


UserSessionRepositoryDep = Annotated[
    UserSessionRepositoryProtocol, Depends(get_user_session_repository)
]
