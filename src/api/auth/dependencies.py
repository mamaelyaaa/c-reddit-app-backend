from typing import Annotated

from fastapi import Request, Depends

from api.users.schemas import UserReadSchema
from .service import AuthServiceDep


async def get_current_user(
    auth_service: AuthServiceDep,
    request: Request,
) -> UserReadSchema:
    current_user = await auth_service.get_current_user(request)
    return current_user


async def get_active_user(
    auth_service: AuthServiceDep,
    request: Request,
) -> UserReadSchema:
    active_user = await auth_service.get_active_user(request)
    return active_user


async def get_superuser(
    auth_service: AuthServiceDep,
    request: Request,
) -> UserReadSchema:
    superuser = await auth_service.get_superuser(request)
    return superuser


CurrentUserDep = Annotated[UserReadSchema, Depends(get_current_user)]
ActiveUserDep = Annotated[UserReadSchema, Depends(get_active_user)]
SuperuserDep = Annotated[UserReadSchema, Depends(get_superuser)]
