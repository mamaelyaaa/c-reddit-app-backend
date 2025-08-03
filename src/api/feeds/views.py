from fastapi import APIRouter, Depends

from api.auth import ActiveUserDep
from api.auth.views import http_bearer
from core.dependencies import PaginationDep, FiltersDep
from schemas import SearchResponseSchema
from .schemas import FeedDetailSchema
from .service import FeedServiceDep

router = APIRouter(prefix="/feed", tags=["Лента"], dependencies=[Depends(http_bearer)])


@router.get("", response_model=SearchResponseSchema[FeedDetailSchema])
async def get_user_events(
    active_user: ActiveUserDep,
    feed_service: FeedServiceDep,
    pagination: PaginationDep,
):
    events = await feed_service.get_user_events(user_id=active_user.id, pagination=pagination)
    return events
