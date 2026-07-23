import enum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"



class User(BaseModel):
    __tablename__ = "users"


    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )


    hashed_password: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )


    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )


    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role"),
        default=UserRole.MEMBER,
        nullable=False
    )


    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )


    # Google OAuth fields

    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        index=True
    )


    avatar_url: Mapped[str | None] = mapped_column(
        String(1000),
        nullable=True
    )


    # Relationships

    documents: Mapped[list["Document"]] = relationship(
        back_populates="owner"
    )


    chats: Mapped[list["Chat"]] = relationship(
        back_populates="user"
    )