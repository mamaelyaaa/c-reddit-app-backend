from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from api.comments.schemas import CommentReadSchema, CommentSummaryReadSchema


class PostBaseSchema(BaseModel):
    title: str
    description: Optional[str]


class PostCreateSchema(PostBaseSchema):
    pass


class PostReadSchema(PostBaseSchema):
    id: int

    comments_count: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostDetailSchema(PostReadSchema):
    comments: list[CommentSummaryReadSchema]


class PostUpdateSchema(PostBaseSchema):
    pass


class PostUpdatePartialSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
