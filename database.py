"""Модуль инициализации базы данных и сессий."""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from models import Base
from utils import user_data_path


DATABASE_URL = f"sqlite:///{user_data_path('todo.db')}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


def init_db() -> None:
    """
    Инициализирует схему БД и добавляет отсутствующие колонки.
    """
    Base.metadata.create_all(engine)
    inspector = inspect(engine)
    
    with engine.connect() as conn:
        # Проверяем и добавляем колонку deadline
        columns = [col['name'] for col in inspector.get_columns('tasks')]
        if 'deadline' not in columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN deadline TIMESTAMP"))
        if 'saved_deadline' not in columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN saved_deadline TIMESTAMP"))
        conn.commit()