from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import UniqueConstraint, ForeignKey
from sqlalchemy.types import String

from models import Base, DateMixin

if TYPE_CHECKING:
    from api.auth.users.models import User
    from api.comments.models import Comment


class Post(Base, DateMixin):
    __tablename__ = "posts"
    __table_args__ = (
        UniqueConstraint(
            "title",
            "user_id",
            name="unique_title_with_user",
        ),
    )

    # Колонки
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(128))
    description: Mapped[Optional[str]] = mapped_column(String(2048))

    # Отношения
    user: Mapped["User"] = relationship(back_populates="posts")
    comments: Mapped[list["Comment"]] = relationship(back_populates="post")

    # Дополнительно
    repr_cols_num = 2
