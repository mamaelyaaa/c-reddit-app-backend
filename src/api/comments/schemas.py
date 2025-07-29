from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from api.auth.users.schemas import UserSummaryReadSchema


class CommentBaseSchema(BaseModel):
    """Базовая схема для комментария"""

    content: str


class CommentCreateSchema(CommentBaseSchema):
    """Схема для создания комментария"""

    pass


class CommentReadSchema(CommentBaseSchema):
    """Схема для чтения комментария из базы"""

    id: int
    post_id: int
    author: UserSummaryReadSchema
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentSummaryReadSchema(CommentBaseSchema):
    """Схема для краткого чтения комментария из базы"""

    id: int
    author: UserSummaryReadSchema
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommentUpdateSchema(CommentBaseSchema):
    """Схема для обновления комментария"""

    content: str = Field(le=2048)
