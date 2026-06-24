"""Модели данных SQLAlchemy."""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, DateTime
from datetime import datetime


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass

class GroupTask(Base):
    """Модель подгруппы задач."""
    __tablename__ = "groups"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    title: Mapped[str]
    description: Mapped[str]
    
    parent: Mapped["GroupTask | None"] = relationship(
        "GroupTask", back_populates="children", remote_side=[id]
    )
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    
    children: Mapped[list["GroupTask"]] = relationship(
        "GroupTask", back_populates="parent", cascade="all, delete-orphan"
    )

    tasks: Mapped[list["Task"]] = relationship(back_populates="group", cascade="all, delete-orphan")

    @property
    def progress(self) -> tuple[int, int]:
        """Возвращает кортеж (выполнено, всего) для отображения прогресса."""
        total = 0
        done = 0
        
        # Считаем прямые задачи
        for task in self.tasks:
            total += 1
            if task.is_done:
                done += 1
                
        # Рекурсивно считаем задачи в дочерних группах
        for child in self.children:
            c_done, c_total = child.progress
            total += c_total
            done += c_done
            
        return done, total

    

class Task(Base):
    """Модель задачи пользователя."""
    __tablename__ = "tasks"
    
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    group_id: Mapped[int | None] = mapped_column(ForeignKey("groups.id"), nullable=True)
    group: Mapped["GroupTask | None"] = relationship(back_populates="tasks")
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    is_done: Mapped[bool] = mapped_column(default=False)
    deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    saved_deadline: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_notifier: Mapped[int | None] = mapped_column(default = None)

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