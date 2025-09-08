import pytest

from api.users.models import User
from api.users.repository import get_user_repository


async def test_user_create(db_session):
    user_repo = get_user_repository(db_session)

    user_id = await user_repo.create(
        data={
            "email": "user123@example.com",
            "password": "qwerty123",
            "username": "user",
        }
    )
    assert user_id == 1


async def test_user_read(db_session):
    user = User(username="user", email="user123@example.com", password="qwerty123")
    db_session.add(user)
    await db_session.commit()

    user_repo = get_user_repository(db_session)
    # founded_user = await user_repo.read_one(id=1)
    # assert user == founded_user