"""Главный модуль приложения TodoApp."""
import json
import os
import customtkinter as ctk
from tkinter import messagebox
from sqlalchemy.exc import IntegrityError

from database import Session, init_db
from auth import AuthService
from tasks import TaskManager
from models import User
from utils import user_data_path
from .helpers import center_window, bring_to_front
from .auth_view import AuthView
from .task_view import TaskView


# Настройка темы до создания виджетов
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class TodoApp:
    """Основной класс приложения."""
    
    def __init__(self):
        # Инициализация БД и сервисов
        init_db()
        self.session = Session()
        self.auth_service = AuthService(self.session)
        self.task_manager = TaskManager(self.session)
        self.current_user: User | None = None

        # Настройка главного окна
        self.root = ctk.CTk()
        self.root.title("Todo List")
        self.root.geometry("900x700")
        center_window(self.root, 900, 700)
        self.root.resizable(True, True)

        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Инициализация представлений
        self.auth_view = AuthView(
            main_frame=self.main_frame,
            root=self.root,
            auth_service=self.auth_service,
            on_login_success=self._on_login_success,
            on_show_tasks=self.show_tasks
        )
        self.task_view: TaskView | None = None

        # Авто-вход или показ экрана входа
        if not self._try_auto_login():
            self.auth_view.show_login()

        bring_to_front(self.root)
        self.root.mainloop()

    def _on_login_success(self, user: User, email: str) -> None:
        """Вызывается при успешном входе."""
        self.current_user = user
        self._save_session(email)

    # ---------- Работа с сессией ----------
    def _save_session(self, email: str) -> None:
        """Сохраняет email пользователя в файл сессии."""
        with open(user_data_path("session.json"), "w") as f:
            json.dump({"email": email}, f)

    def _load_session(self) -> str | None:
        """Загружает сохраненный email из файла сессии."""
        try:
            with open(user_data_path("session.json"), "r") as f:
                data = json.load(f)
                return data.get("email")
        except Exception:
            return None

    def _clear_session(self) -> None:
        """Удаляет файл сессии."""
        try:
            os.remove(user_data_path("session.json"))
        except Exception:
            pass

    def _try_auto_login(self) -> bool:
        """Пытается автоматически войти по сохраненной сессии."""
        email = self._load_session()
        if email:
            user = self.session.query(User).filter_by(email=email).first()
            if user:
                self.current_user = user
                self.show_tasks()
                return True
            self._clear_session()
        return False

    # ---------- Навигация ----------
    def show_tasks(self) -> None:
        """Показывает экран управления задачами."""
        if not self.current_user:
            return
            
        self.task_view = TaskView(
            main_frame=self.main_frame,
            root=self.root,
            task_manager=self.task_manager,
            user_id=self.current_user.nickname,
            on_logout=self.logout,
            on_refresh=lambda: None  # refresh вызывается внутри TaskView
        )
        self.task_view.show()

    def logout(self) -> None:
        """Выполняет выход из аккаунта."""
        self.current_user = None
        self._clear_session()
        self.auth_view.show_login()