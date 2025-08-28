from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def new_user_post() -> dict[str, str]:
    return {"title": "Новый пост ура!", "description": "Отличный день йоу"}


class TestPostCreation:
    # TODO Сделать проверку брокера сообщений

    def test_post_creation_success(
        self,
        client: TestClient,
        auth_client_headers: dict[str, str],
        new_user_post: dict[str, str],
    ):
        resp = client.post(
            url="/api/posts", json=new_user_post, headers=auth_client_headers
        )
        assert resp.status_code == 201
        assert "post_id" in resp.json()

    @pytest.mark.parametrize(
        ["post_data", "status_code", "expected_answer"],
        [
            (
                # 1. Пост с идентичным названием уже существует
                {"title": "Новый пост ура!", "description": ""},
                400,
                "Пост с таким названием уже существует",
            ),
            (
                # 2. Превышено количество символов в названии поста
                {"title": "Название" * 120, "description": ""},
                422,
                "Ошибка валидации данных",
            ),
            (
                # 3. Превышено количество символов в описании поста
                {"title": "Новый пост", "description": "Да" * 1500},
                422,
                "Ошибка валидации данных",
            ),
        ],
    )
    def test_post_creation(
        self,
        client: TestClient,
        auth_client_headers: dict[str, str],
        post_data: dict[str, str],
        status_code: int,
        expected_answer: str,
    ):
        resp = client.post(
            url="/api/posts",
            json=post_data,
            headers=auth_client_headers,
        )
        assert resp.status_code == status_code
        assert resp.json()["detail"] == expected_answer


class TestPostRead:

    def test_read_all_user_posts_success(
        self,
        client: TestClient,
        auth_client_headers: dict[str, str],
        new_user_post: dict[str, Any],
    ):
        resp = client.get(url="/api/posts", headers=auth_client_headers)
        assert resp.status_code == 200

        assert resp.json() == {
            "detail": [new_user_post | {"id": 1, "comments_count": 0}],
            "pagination": {"limit": 10, "page": 1},
            "total_found": 1,
        }


class TestPostUpdate:
    pass


class TestPostDelete:
    pass
