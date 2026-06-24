"""Модуль инициализации базы данных и сессий."""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from models import Base
from utils import user_data_path


DATABASE_URL = f"sqlite:///{user_data_path('todo.db')}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

def init_db() -> None:
    """Создание таблиц и миграция схемы при необходимости."""
    Base.metadata.create_all(engine)
    inspector = inspect(engine)

    # Миграции для таблицы users
    user_columns = [col["name"] for col in inspector.get_columns("users")]
    with engine.connect() as conn:
        if "nickname" not in user_columns:
            conn.execute(text("ALTER TABLE users ADD COLUMN nickname TEXT"))
        conn.commit()

    # Миграции для таблицы tasks
    task_columns = [col["name"] for col in inspector.get_columns("tasks")]
    with engine.connect() as conn:
        if "group_id" not in task_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN group_id INTEGER"))
        if "deadline" not in task_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN deadline TIMESTAMP"))
        if "saved_deadline" not in task_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN saved_deadline TIMESTAMP"))
        if "last_notifier" not in task_columns:
            conn.execute(text("ALTER TABLE tasks ADD COLUMN last_notifier INTEGER"))
        conn.commit()