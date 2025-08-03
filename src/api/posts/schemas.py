from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from api.comments.schemas import CommentSummaryReadSchema


class PostBaseSchema(BaseModel):
    title: str
    description: Optional[str]


class PostCreateSchema(PostBaseSchema):
    pass


class PostReadSchema(PostBaseSchema):
    id: int

    comments: list[CommentSummaryReadSchema]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PostSummarySchema(PostBaseSchema):
    id: int
    comments_count: int

    model_config = ConfigDict(from_attributes=True)


class PostUpdateSchema(PostBaseSchema):
    pass


class PostUpdatePartialSchema(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
