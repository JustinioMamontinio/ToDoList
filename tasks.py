"""Менеджер задач: добавление, получение, обновление, удаление."""
from models import Task
from sqlalchemy.orm import Session
from datetime import datetime


class TaskManager:
    """Управление задачами пользователя."""
    
    def __init__(self, session: Session):
        self.session = session

    def add_task(
        self, 
        user_id: int, 
        title: str, 
        description: str, 
        deadline: datetime | None = None
    ) -> None:
        """Создает новую задачу для пользователя."""
        new_task = Task(
            user_id = user_id,
            title = title,
            description  =description,
            deadline = deadline
        )
        self.session.add(new_task)
        self.session.commit()

    def get_all_tasks(self, user_id: int) -> list[Task]:
        """
        Возвращает задачи пользователя в порядке приоритета:
        1. Невыполненные с дедлайном (сортировка: ближайший → дальний, затем по названию)
        2. Невыполненные без дедлайна (по названию)
        3. Выполненные (по названию)
        """
        tasks = self.session.query(Task).filter_by(user_id=user_id).all()

        # Группировка задач по статусу
        not_done_with_deadline = [t for t in tasks if not t.is_done and t.deadline]
        not_done_no_deadline = [t for t in tasks if not t.is_done and not t.deadline]
        done = [t for t in tasks if t.is_done]

        # Сортировка внутри групп
        not_done_with_deadline.sort(key = lambda t: (t.deadline, t.title.lower()))
        not_done_no_deadline.sort(key = lambda t: t.title.lower())
        done.sort(key = lambda t: t.title.lower())

        return not_done_with_deadline + not_done_no_deadline + done

    def toggle_completed(self, user_id: int, task_id: int) -> bool:
        """
        Переключает статус выполнения задачи.
        При выполнении сохраняет дедлайн в saved_deadline.
        """
        task = self.session.get(Task, task_id)
        if not task or task.user_id != user_id:
            return False

        if not task.is_done:
            task.is_done = True
            if task.deadline:
                task.saved_deadline = task.deadline
                task.deadline = None
        else:
            task.is_done = False
            if task.saved_deadline:
                task.deadline = task.saved_deadline
                task.saved_deadline = None
                
        self.session.commit()
        return True

    def delete_task(self, user_id: int, task_id: int) -> bool:
        """Удаляет задачу, если она принадлежит пользователю."""
        task = self.session.get(Task, task_id)
        if task and task.user_id == user_id:
            self.session.delete(task)
            self.session.commit()
            return True
        return False

    def update_deadline(self, task_id: int, deadline: datetime | None) -> bool:
        """Обновляет дедлайн задачи."""
        task = self.session.get(Task, task_id)
        if not task:
            return False
            
        task.deadline = deadline
        if not task.is_done:
            task.saved_deadline = None
        self.session.commit()
        return True