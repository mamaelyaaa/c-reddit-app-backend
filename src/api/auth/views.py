from fastapi import (
    APIRouter,
    Depends,
    Request,
    Response,
    status,
)
from fastapi.security import HTTPBearer

from api.users.schemas import (
    UserRegisterSchema,
    UserLoginSchema,
)
from schemas import BaseResponseIdSchema
from .dependencies import ActiveUserDep, get_active_user
from .schemas import BearerResponseSchema
from .service import AuthServiceDep

router = APIRouter(prefix="/auth", tags=["Авторизация"])

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
    dependencies=[Depends(http_bearer), Depends(get_active_user)],
)
async def logout_user(
    auth_service: AuthServiceDep,
    request: Request,
    response: Response,
):
    await auth_service.logout_user(request, response)
    return


@router.delete(
    "/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(http_bearer), Depends(get_active_user)],
)
async def revoke_all_sessions(
    auth_service: AuthServiceDep,
    request: Request,
    response: Response,
):
    await auth_service.revoke_sessions(request, response)
    return
