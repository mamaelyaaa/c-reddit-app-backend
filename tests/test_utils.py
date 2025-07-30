import pytest

from utils.security import hash_password, verify_passwords


@pytest.fixture(scope="module")
async def password() -> str:
    return "qwerty123"


@pytest.fixture(scope="module")
async def hash_pwd(password) -> str:
    pwd = await hash_password(password)
    return pwd


@pytest.mark.asyncio
@pytest.mark.skip
async def test_hash_password(password, hash_pwd):
    assert hash_pwd != password
    assert hash_pwd != await hash_password(password)


@pytest.mark.asyncio
@pytest.mark.skip
async def test_verify_password(password, hash_pwd):
    assert await verify_passwords(password, hash_pwd) == True
    assert await verify_passwords(password + "123", hash_pwd) == False
