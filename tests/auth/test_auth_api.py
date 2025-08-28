from typing import Any

import pytest
from fastapi.testclient import TestClient


class TestAuthRegister:
    def test_user_success_register(self, client: TestClient):
        user_data = {
            "email": "user123@example.com",
            "password": "qwerty123",
            "username": "user",
            "is_superuser": False,
        }
        resp = client.post("/api/users/register", json=user_data)
        assert resp.status_code == 201

    @pytest.mark.parametrize(
        ["data", "status_code", "expected_ans"],
        [
            (
                # 1. Регистрация на существующую почту (по юзернейму)
                {
                    "email": "newuser123@example.com",
                    "password": "qwerty123",
                    "username": "user",
                    "is_superuser": False,
                },
                400,
                {
                    "detail": "Пользователь с такими параметрами уже существует",
                },
            ),
            (
                # 2. Регистрация на существующую почту (по почте)
                {
                    "email": "user123@example.com",
                    "password": "qwerty123",
                    "username": "user123",
                    "is_superuser": False,
                },
                400,
                {
                    "detail": "Пользователь с такими параметрами уже существует",
                },
            ),
            (
                # 3. Невалидная почта
                {
                    "email": "user1232example.com",
                    "password": "qwerty123",
                    "username": "user",
                    "is_superuser": False,
                },
                422,
                {
                    "detail": "Ошибка валидации данных",
                    "errors": [
                        {
                            "field": "body.email",
                            "message": "value is not a valid email address: An email address must have an "
                            "@-sign.",
                            "type": "value_error",
                        }
                    ],
                },
            ),
            (
                # 4. Слишком короткий пароль
                {
                    "email": "new_user123@example.com",
                    "password": "1",
                    "username": "newuser",
                    "is_superuser": False,
                },
                400,
                {
                    "detail": "Пароль должен содержать не менее 6 символов",
                },
            ),
            (
                # 5. Нехватка данных
                {
                    "email": "new_user123@example.com",
                    "password": "qwerty123",
                    "is_superuser": False,
                },
                422,
                {
                    "detail": "Ошибка валидации данных",
                    "errors": [
                        {
                            "field": "body.username",
                            "message": "Field required",
                            "type": "missing",
                        },
                    ],
                },
            ),
        ],
    )
    def test_user_register_diff(
        self,
        client: TestClient,
        data: dict[str, str],
        status_code: int,
        expected_ans: str | list[dict],
    ):
        resp = client.post("/api/users/register", json=data)
        assert resp.status_code == status_code
        assert resp.json() == expected_ans


class TestAuthLogin:
    def test_user_success_login(self, client: TestClient):
        user_data = {
            "email": "user123@example.com",
            "password": "qwerty123",
            "username": "user",
        }
        resp = client.post("/api/users/login", json=user_data)
        assert resp.status_code == 200
        assert "access_token" in resp.json() and resp.json()["token_type"] == "Bearer"

    @pytest.mark.parametrize(
        ["data", "status_code", "expected_ans"],
        [
            (
                # 1. Неправильная почта
                {
                    "email": "different_user123@example.com",
                    "password": "qwerty123",
                    "username": "user",
                },
                401,
                {"detail": "Неправильная почта или юзернейм"},
            ),
            (
                # 2. Неправильный пароль
                {
                    "email": "user123@example.com",
                    "password": "wrong_password",
                    "username": "user",
                },
                401,
                {"detail": "Неправильный пароль"},
            ),
            (
                # 3. Неправильный юзернейм
                {
                    "email": "user123@example.com",
                    "password": "qwerty123",
                    "username": "123",
                },
                401,
                {"detail": "Неправильная почта или юзернейм"},
            ),
        ],
    )
    def test_user_login(
        self,
        client: TestClient,
        data: dict[str, str],
        status_code: int,
        expected_ans: dict[str, Any],
    ):
        resp = client.post("/api/users/login", json=data)
        assert resp.status_code == status_code
        assert resp.json() == expected_ans


@pytest.fixture(scope="session")
def access_token(client: TestClient) -> str:
    user_data = {
        "email": "user123@example.com",
        "password": "qwerty123",
        "username": "user",
    }
    resp = client.post("/api/users/login", json=user_data)
    assert resp.status_code == 200
    return resp.json()["access_token"]


class TestAuthRefreshOldToken:
    def test_user_success_refresh(
        self,
        client: TestClient,
        auth_client_headers: dict[str, str],
    ):
        resp = client.get("/api/users/refresh", headers=auth_client_headers)
        assert resp.status_code == 200
        assert resp.json()["token_type"] == "Bearer"
        assert resp.json()["access_token"] != auth_client_headers["Authorization"]

    @pytest.mark.parametrize(
        ["headers", "status_code", "expected_ans"],
        [
            (
                # 1. Невалидный для декодирования токен
                {
                    "Authorization": f"Bearer 123",
                },
                401,
                {"detail": "Невалидный токен для расшифровки"},
            ),
            (
                # 2. Невалидный заголовок (ключ)
                {
                    "Authorization-Header": f"Bearer {access_token}",
                },
                403,
                {"detail": "Отсутствует токен доступа в запросе к платформе"},
            ),
            (
                # 3. Невалидный заголовок (отсутствие типа токена)
                {
                    "Authorization": f"{access_token}",
                },
                401,
                {"detail": "Невалидный токен для расшифровки"},
            ),
            (
                # 4. Отсутствие заголовков
                {},
                403,
                {"detail": "Отсутствует токен доступа в запросе к платформе"},
            ),
        ],
    )
    def test_user_refresh(
        self,
        client: TestClient,
        access_token: str,
        headers: dict[str, Any],
        status_code: int,
        expected_ans: dict[str, Any],
    ):
        resp = client.get("/api/users/refresh", headers=headers)
        assert resp.status_code == status_code
        assert resp.json() == expected_ans


class TestAuthLogout:
    pass


class TestAuthRevokeTokens:
    pass


class TestAuthGet:
    pass
