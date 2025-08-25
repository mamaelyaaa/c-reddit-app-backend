from pydantic import BaseModel, ConfigDict

from api.posts.schemas import PostSummarySchema
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
    post: PostSummarySchema

    model_config = ConfigDict(from_attributes=True)
