from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

if TYPE_CHECKING:
    from api.users.models import User
    from api.posts.models import Post


class UserFeed(Base):
    __tablename__ = "users_feed"
    __table_args__ = (
        UniqueConstraint(
            "author_id",
            "recipient_id",
            "post_id",
        ),
    )
    repr_cols_num = 5

    # Колонки
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))

    # Отношения
    author: Mapped["User"] = relationship(
        backref="feeds",
        primaryjoin="UserFeed.author_id == User.id",
    )
    post: Mapped["Post"] = relationship(backref="feed")
