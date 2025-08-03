from pydantic import BaseModel, ConfigDict

from api.posts.schemas import PostReadSchema
from api.users.schemas import UserSummaryReadSchema


class FeedBaseSchema(BaseModel):
    author_id: int
    post_id: int


class FeedCreateSchema(FeedBaseSchema):
    pass


class FeedReadSchema(FeedBaseSchema):
    model_config = ConfigDict(from_attributes=True)


class FeedDetailSchema(BaseModel):
    author: UserSummaryReadSchema
    post: PostReadSchema

    model_config = ConfigDict(from_attributes=True)
