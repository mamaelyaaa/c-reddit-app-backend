import logging
from typing import Protocol, Any, Optional, Sequence

from sqlalchemy import select, Result, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class RepositoryProtocol[Model](Protocol):

    async def create(self, data: dict[str, Any]) -> int:
        """
        Создание сущности
        :return: id сущности
        """
        pass

    async def read_one(self, *args, **kwargs) -> Optional[Model]:
        """Поиск одной сущности по параметрам"""
        pass

    async def read_all(
        self, limit: Optional[int], offset: Optional[int], *args, **kwargs
    ) -> Sequence[Model]:
        """Поиск сущностей по параметрам"""
        pass

    async def update(self, model: Model, upd: dict[str, Any]) -> Model:
        """Обновление сущности"""
        pass

    async def delete(self, model: Model) -> None:
        """Удаление сущности"""
        pass

    async def count(self, *args, **kwargs) -> int:
        """Поиск количества сущностей по параметрам"""
        pass

    async def check_exists(self, *args, **kwargs) -> bool:
        """Проверка существования сущности"""
        pass


class SQLAlchemyRepository[Model]:
    model: Model

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> int:
        m = self.model(**data)
        logger.debug("Создаем новую сущность %s ...", m)
        self.session.add(m)
        await self.session.commit()
        return m.id

    async def read_one(self, *args, **kwargs) -> Optional[Model]:
        logger.debug("Ищем сущность %s ...", self.model.__name__)
        query = select(self.model).filter_by(**kwargs)
        res: Result = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def read_all(
        self,
        limit: Optional[int],
        offset: Optional[int],
        *args,
        **kwargs,
    ) -> Sequence[Model]:
        query = select(self.model).filter_by(**kwargs)
        if limit:
            query = query.limit(limit)
        if offset:
            query = query.offset(offset)
        res: Result = await self.session.execute(query)
        return res.scalars().all()

    async def update(self, model: Model, upd: dict[str, Any]) -> Model:
        for col, value in upd.items():
            if not hasattr(model, col):
                await self.session.rollback()
                raise

            setattr(model, col, value)

        await self.session.commit()
        await self.session.refresh(model)
        return model

    async def delete(self, model: Model) -> None:
        await self.session.delete(model)
        await self.session.commit()
        return

    async def count(self, *args, **kwargs) -> int:
        query = select(func.count(self.model.id)).filter_by(**kwargs)
        res = await self.session.execute(query)
        return res.scalar_one()

    async def check_exists(self, *args, **kwargs) -> bool:
        query = select(self.model.id).filter_by(**kwargs)
        res = await self.session.execute(query)
        return len(res.scalars().all()) > 0
