import logging
from typing import AsyncGenerator

from asyncpg.exceptions import ConnectionDoesNotExistError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)

from .config import settings
from .exceptions import UnavailableServiceException

logger = logging.getLogger(__name__)


class Database:

    def __init__(
        self,
        url: str,
        echo: bool,
        pool_size: int = 10,
        max_overflow: int = 20,
        pool_recycle: int = 3600,
        pool_pre_ping=True,
    ):
        self._engine = create_async_engine(
            url=url,
            echo=echo,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_pre_ping=pool_pre_ping,
        )
        self._session_factory = async_sessionmaker(
            bind=self._engine, expire_on_commit=False, autoflush=False
        )

    async def dispose(self) -> None:
        logger.info("Подключение к базе данных разорвано")
        await self._engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        async with self._session_factory() as session:
            try:
                yield session
            except ConnectionDoesNotExistError as e:
                raise UnavailableServiceException(str(e))

    @property
    def get_session_factory(self):
        return self._session_factory


db_helper = Database(url=str(settings.db.POSTGRES_DSN), echo=bool(settings.db.echo))
