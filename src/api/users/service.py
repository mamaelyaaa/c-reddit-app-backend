from typing import Protocol

from api.users.schemas import UserReadSchema
from schemas import PaginationSchema, SearchResponseSchema


class UserServiceProtocol(Protocol):

    async def get_user_by_user_id(self, user_id: int) -> UserReadSchema:
        """Получает информацию о пользователе в системе вместе с сокращенными постами"""
        pass

    async def get_users(self, pagination: PaginationSchema) -> SearchResponseSchema[UserReadSchema]:
        """Получает список пользователей с пагинацией без постов"""
        pass

