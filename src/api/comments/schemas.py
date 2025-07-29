from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict


class CommentBaseSchema(BaseModel):
    """Базовая схема для комментария"""

    post_id: int
    user_id: int
    comment: str = Field(le=2048)


class CommentCreateSchema(CommentBaseSchema):
    """Схема для создания комментария"""

    pass


class CommentReadSchema(CommentBaseSchema):
    """Схема для чтения комментария из базы"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
