from typing import Generator, Any

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient

from src.core import settings, db_helper
from src.main import app


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
def client(apply_migrations) -> Generator[TestClient, Any, None]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="package")
def access_token(client):
    user_data = {
        "email": "user123@example.com",
        "password": "qwerty123",
        "username": "user",
    }
    resp = client.post("/api/users/login", json=user_data)
    assert resp.status_code == 200
    yield resp.json()["access_token"]


@pytest.fixture(scope="package")
def auth_client_headers(access_token: str) -> dict[str, str]:
    headers = {"Authorization": f"Bearer {access_token}"}
    return headers
