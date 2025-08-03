from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Text

from models import DateMixin, Base

if TYPE_CHECKING:
    from api.posts.models import Post
    from api.users.models import User


class Comment(Base, DateMixin):
    __tablename__ = "comments"

    # Колонки
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)

    # Отношения
    post: Mapped["Post"] = relationship(back_populates="comments")
    author: Mapped["User"] = relationship(backref="comment")
