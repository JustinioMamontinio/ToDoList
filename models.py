"""Модели данных SQLAlchemy."""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


class Task(Base):
    """Модель задачи пользователя."""
    __tablename__ = "tasks"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    is_done: Mapped[bool] = mapped_column(default=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    saved_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    def __str__(self) -> str:
        return f'[{"V" if self.is_done else "X"}]   {self.title}'

    def complete(self) -> None:
        """Отметить задачу как выполненную."""
        self.is_done = True


class User(Base):
    """Модель пользователя."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    nickname: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(unique=True)
    password_hash: Mapped[str]