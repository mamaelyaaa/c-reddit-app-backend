from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
)
from fastapi.security import HTTPBearer

from schemas import BaseResponseIdSchema
from .dependencies import ActiveUserDep, CurrentUserDep
from .jwt.schemas import BearerResponseSchema
from .service import AuthServiceDep
from .users.schemas import (
    UserReadSchema,
    UserUpdatePartialSchema,
    UserRegisterSchema,
    UserLoginSchema,
)

router = APIRouter(prefix="/users", tags=["Авторизация"])

http_bearer = HTTPBearer(auto_error=False)


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponseIdSchema,
)
async def register_user(auth_service: AuthServiceDep, user_data: UserRegisterSchema):
    user_id = await auth_service.register_user(user_data)
    return user_id


@router.post("/login", response_model=BearerResponseSchema)
async def login_user(
    auth_service: AuthServiceDep, user_data: UserLoginSchema, response: Response
):
    access_token = await auth_service.login_user(user_data, response)
    return access_token


@router.get(
    "/refresh",
    response_model=BearerResponseSchema,
    dependencies=[Depends(http_bearer)],
)
async def refresh_access_token(auth_service: AuthServiceDep, request: Request):
    new_access_token = await auth_service.refresh_token(request)
    return new_access_token


@router.delete(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(http_bearer)],
)
async def login_user(
    auth_service: AuthServiceDep,
    response: Response,
    request: Request,
):
    await auth_service.logout_user(response, request)
    return


@router.get("/me", response_model=UserReadSchema, dependencies=[Depends(http_bearer)])
async def get_current_user(current_user: CurrentUserDep):
    return current_user


@router.patch("/me", response_model=UserReadSchema, dependencies=[Depends(http_bearer)])
async def current_user_partial_update(
    active_user: ActiveUserDep,
    auth_service: AuthServiceDep,
    update_data: UserUpdatePartialSchema,
):
    updated_cur_user = await auth_service.update_user(
        update_user_data=update_data, user_id=active_user.id, partial=True
    )
    return updated_cur_user


@router.put("/me", response_model=UserReadSchema, dependencies=[Depends(http_bearer)])
async def current_user_partial_update(
    active_user: ActiveUserDep,
    auth_service: AuthServiceDep,
    update_data: UserUpdatePartialSchema,
):
    updated_cur_user = await auth_service.update_user(
        update_user_data=update_data, user_id=active_user.id, partial=False
    )
    return updated_cur_user
