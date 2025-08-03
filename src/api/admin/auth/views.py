from fastapi import APIRouter, Depends

from api.admin.auth.schemas import AdminUserUpdateSchema, AdminUserUpdatePartialSchema
from api.auth.dependencies import SuperuserDep, get_superuser
from api.auth.service import AuthServiceDep
from api.auth.views import http_bearer
from api.users.schemas import UserReadSchema

router = APIRouter(
    prefix="/auth",
    dependencies=[
        Depends(http_bearer),
        Depends(get_superuser),
    ],
)


@router.get("/me", response_model=UserReadSchema)
async def get_current_admin(superuser: SuperuserDep):
    return superuser


@router.put("/{user_id}", response_model=UserReadSchema)
async def update_user(
    auth_service: AuthServiceDep,
    user_id: int,
    update_data: AdminUserUpdateSchema,
):
    updated_user = await auth_service.update_user(user_id, update_data, partial=False)
    return updated_user


@router.patch("/{user_id}", response_model=UserReadSchema)
async def update_user_partially(
    auth_service: AuthServiceDep,
    user_id: int,
    update_data: AdminUserUpdatePartialSchema,
):
    updated_user = await auth_service.update_user(user_id, update_data, partial=True)
    return updated_user
