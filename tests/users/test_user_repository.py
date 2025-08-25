from typing import Any

import pytest

from api.users.repository import UserRepository, UserRepositoryProtocol
from api.users.schemas import UserRegisterSchema


@pytest.fixture(scope="package")
def user_repository(db_session) -> UserRepositoryProtocol:
    return UserRepository(db_session)


@pytest.fixture
def user() -> dict[str, Any]:
    return {
        "username": "oleg228",
        "email": "oleg@example.com",
        "password": "qwerty123",
        "is_superuser": False,
    }


# @pytest.mark.asyncio
# async def test_user_create(user_repository: UserRepositoryProtocol, user):
#     user_id = await user_repository.add_user(UserRegisterSchema(**user))
#     assert user_id == 1


# @pytest.mark.asyncio
# async def test_user_read(user_repository: UserRepositoryProtocol, user):
#     user = await user_repository.get_user(id=1)
#     # assert user_id == 1
#     print(user)
