from fastapi import APIRouter, status, Depends

from api.auth import ActiveUserDep, http_bearer
from schemas import BaseResponseSchema
from .service import FollowsServiceDep

router = APIRouter(
    prefix="/follows", tags=["Подписки"], dependencies=[Depends(http_bearer)]
)


@router.post(
    "/{target_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=BaseResponseSchema,
)
async def subscribe_user(
    active_user: ActiveUserDep,
    follows_service: FollowsServiceDep,
    target_id: int,
):
    # Подписываемся на пользователя
    follow_id = await follows_service.subscribe_user(
        cur_user_id=active_user.id, target_id=target_id
    )

    return BaseResponseSchema(
        detail=f"Пользователь #{active_user.id} успешно подписался на пользователя #{target_id}"
    )


@router.delete(
    "/{target_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unsubscribe_user(
    active_user: ActiveUserDep, follows_service: FollowsServiceDep, target_id: int
):
    await follows_service.unsubscribe_user(
        cur_user_id=active_user.id, target_id=target_id
    )

    return
