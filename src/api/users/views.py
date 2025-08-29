from fastapi import APIRouter, Depends

from api.auth import http_bearer, CurrentUserDep, ActiveUserDep
from .schemas import UserReadSchema, UserUpdatePartialSchema
from .service import UserServiceDep

router = APIRouter(
    prefix="/users", tags=["Пользователь"], dependencies=[Depends(http_bearer)]
)


@router.get("/me", response_model=UserReadSchema)
async def get_current_user(current_user: CurrentUserDep):
    return current_user


@router.patch("/me", response_model=UserReadSchema)
async def current_user_partial_update(
    active_user: ActiveUserDep,
    user_service: UserServiceDep,
    update_data: UserUpdatePartialSchema,
):
    updated_cur_user = await user_service.update_user(
        user_id=active_user.id,
        upd_user=update_data,
        partial=True,
    )
    return updated_cur_user


@router.put("/me", response_model=UserReadSchema)
async def current_user_update(
    active_user: ActiveUserDep,
    user_service: UserServiceDep,
    update_data: UserUpdatePartialSchema,
):
    updated_cur_user = await user_service.update_user(
        user_id=active_user.id,
        upd_user=update_data,
        partial=False,
    )
    return updated_cur_user
