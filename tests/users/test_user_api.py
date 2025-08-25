from typing import Any

import pytest
from fastapi.testclient import TestClient


class TestUserRegister:
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


class TestUserLogin:
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
                {"detail": "Неправильная почта"},
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
                {"detail": "Неправильный юзернейм"},
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
        print(resp.json())
        assert resp.status_code == status_code
        assert resp.json() == expected_ans


# class TestUserRefreshOldToken:
#     def test_user_success_refresh(self, client: TestClient):
#         headers = {"Authorization": "Bearer 123"}
#         resp = client.get("/api/users/refresh", headers=headers)
#         print(resp.json())
#         assert resp.status_code == 200
#         assert "access_token" in resp.json() and resp.json()["token_type"] == "Bearer"
