from typing import Protocol, Any, Optional, Sequence, TypeVar

from sqlalchemy import select, Result
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase, DeclarativeMeta

from core.dependencies import SessionDep

ModelType = TypeVar("ModelType", bound=DeclarativeMeta)


class RepositoryProtocol(Protocol):

    async def create(self, data: dict[str, Any]) -> ModelType:
        pass

    async def read_one(self, *args, **kwargs) -> Optional[ModelType]:
        pass

    async def read_all(self, *args, **kwargs) -> Sequence[ModelType]:
        pass

    async def update(self, model: ModelType, upd: dict[str, Any]) -> ModelType:
        pass

    async def delete(self, model: ModelType) -> None:
        pass


class SQLAlchemyRepository[Model]:
    model: type[ModelType] = None

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: dict[str, Any]) -> Model:
        m = self.model(**data)
        self.session.add(m)
        await self.session.commit()
        return m.id

    async def read_one(self, *args, **kwargs) -> Optional[Model]:
        query = select(self.model).filter_by(**kwargs)
        res: Result = await self.session.execute(query)
        return res.scalar_one_or_none()

    async def read_all(self, *args, **kwargs) -> Sequence[Model]:
        query = select(self.model).filter_by(**kwargs)
        res: Result = await self.session.execute(query)
        return res.scalars().all()

    async def update(self, model: Model, upd: dict[str, Any]) -> Model:
        for col, value in upd.items():
            if not hasattr(model, col):
                await self.session.rollback()
                raise

            setattr(model, col, value)

        await self.session.commit()
        return model

    async def delete(self, model: Model) -> None:
        await self.session.delete(model)
        await self.session.commit()
        return


def get_base_repository(session: SessionDep) -> RepositoryProtocol:
    return SQLAlchemyRepository(session)
