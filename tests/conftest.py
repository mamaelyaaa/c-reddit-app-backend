import asyncio
from typing import Generator, Any

import pytest
import pytest_asyncio

from fastapi.testclient import TestClient

from alembic import command
from alembic.config import Config
from httpx import AsyncClient, ASGITransport

from core import settings, db_helper
from main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_db():
    # startup
    assert settings.run.mode == "TEST"
    assert "_pytest" in settings.db.name or "_test" in settings.db.name

    yield

    # shutdown
    await db_helper.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_session():
    async with db_helper.get_session_factory() as session:
        yield session


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    alembic_cfg = Config(settings.files.alembic_ini)

    alembic_cfg.set_main_option("script_location", str(settings.files.alembic_dir))
    alembic_cfg.set_main_option("sqlalchemy.url", str(settings.db.POSTGRES_DSN))

    command.upgrade(alembic_cfg, "head")

    yield

    command.downgrade(alembic_cfg, "base")


@pytest.fixture(scope="session")
def client() -> Generator[TestClient, Any, None]:
    with TestClient(app) as test_client:
        yield test_client
