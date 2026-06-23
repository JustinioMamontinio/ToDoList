"""Менеджер задач: добавление, получение, обновление, удаление."""
from models import Task, GroupTask
from sqlalchemy.orm import Session, joinedload
from datetime import datetime
from helpers import sort_tasks, sort_groups

class GroupManager:
    def __init__(self, session: Session):
        self.session = session

    def create_group(self, user_id, title, description, parent_id = None):
        if parent_id:
            parent = self.session.query(GroupTask).filter_by(id = parent_id, user_id = user_id).first()
            if not parent:
                raise ValueError("Родительская группа не найдена или недоступна")
        new_group = GroupTask(user_id = user_id, title = title, description = description, parent_id = parent_id)
        self.session.add(new_group)
        self.session.commit()
        return new_group

    def get_root_groups(self, user_id):
        return self.session.query(GroupTask).options(joinedload(GroupTask.children).joinedload(GroupTask.tasks), joinedload(GroupTask.tasks)).filter_by(user_id = user_id, parent_id = None).all()
    
    def delete_group(self, user_id, group_id):
        group = self.session.query(GroupTask).filter_by(id = group_id, user_id = user_id).first()
        if group:
            self.session.delete(group)
            self.session.commit()
            return True
        return False
    
    def move_task_to_group(self, user_id, group_id, task_id):
        task = self.session.query(Task).filter_by(id = task_id, user_id = user_id).first()
        if task:
            if group_id:
                group = self.session.query(GroupTask).filter_by(id = group_id, user_id = user_id).first()
                if not group:
                    return False
            task.group_id = group_id
            self.session.commit()
            return True
        return False
    
    def add_subtask(self, user_id: int, group_id: int, title: str, description: str = "", deadline = None):
        group = self.session.query(GroupTask).filter_by(id=group_id, user_id=user_id).first()
        if not group:
            raise ValueError("Группа не найдена")
        
        new_task = Task(
            user_id=user_id,
            group_id=group_id,
            title=title,
            description=description,
            deadline=deadline
        )
        self.session.add(new_task)
        self.session.commit()
        return new_task

    def get_group(self, user_id, group_id):
        return self.session.query(GroupTask).filter_by(id=group_id, user_id=user_id).first()
        

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
    ) -> Task:
        """Создает новую задачу для пользователя."""
        new_task = Task(
            user_id = user_id,
            title = title,
            description  =description,
            deadline = deadline
        )
        self.session.add(new_task)
        self.session.commit()
        return new_task

    def get_ungrouped_tasks(self, user_id: int) -> list[Task]:
        """
        Возвращает задачи пользователя в порядке приоритета:
        1. Невыполненные с дедлайном (сортировка: ближайший → дальний, затем по названию)
        2. Невыполненные без дедлайна (по названию)
        3. Выполненные (по названию)
        """
        tasks = self.session.query(Task).filter_by(user_id=user_id, group_id = None).all()
        sorted_tasks = sort_tasks(tasks)
        return sorted_tasks

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