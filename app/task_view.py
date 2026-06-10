"""Модуль интерфейса управления задачами."""
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, date, timedelta
from tasks import TaskManager
from models import Task
from .helpers import format_deadline
from .task_card import TaskCard
from .dialogs import DeadlineEditDialog


class TaskView:
    """Управление экраном списка задач."""
    
    def __init__(
        self,
        main_frame: ctk.CTkFrame,
        root: ctk.CTk,
        task_manager: TaskManager,
        user_id: int,
        on_logout: callable,
        on_refresh: callable
    ):
        self.main_frame = main_frame
        self.root = root
        self.task_manager = task_manager
        self.user_id = user_id
        self._on_logout = on_logout
        self._on_refresh = on_refresh
        
        # Виджеты формы добавления задачи
        self.title_entry: ctk.CTkEntry | None = None
        self.desc_entry: ctk.CTkEntry | None = None
        self.deadline_enabled: ctk.IntVar | None = None
        self.deadline_frame: ctk.CTkFrame | None = None
        self.calendar: DateEntry | None = None
        self.hour_entry: ctk.CTkEntry | None = None
        self.minute_entry: ctk.CTkEntry | None = None
        self.tasks_container: ctk.CTkScrollableFrame | None = None

    def show(self) -> None:
        """Отображает экран управления задачами."""
        # Очистка и настройка окна
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        self.root.geometry("950x750")
        self.root.resizable(True, True)

        self._build_header()
        self._build_add_task_form()
        self._build_tasks_list()
        self.refresh()
        
        if self.title_entry:
            self.title_entry.focus()
        self.root.bind('<Return>', lambda e: self.add_task())

    def _build_header(self) -> None:
        """Создает заголовок с приветствием и кнопкой выхода."""
        header = ctk.CTkFrame(self.main_frame, height=50)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header, text=f"Привет, {self.user_id}!",  # ник передается извне
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(side="left", padx=10)
        ctk.CTkButton(header, text="Выйти", command=self._on_logout, width=80).pack(side="right", padx=10)

    def _build_add_task_form(self) -> None:
        """Создает форму добавления новой задачи."""
        form = ctk.CTkFrame(self.main_frame, corner_radius=10)
        form.pack(fill="x", pady=10)

        # Название
        ctk.CTkLabel(form, text="Название:", font=ctk.CTkFont(weight="bold")).grid(
            row=0, column=0, padx=10, pady=(10, 0), sticky="w"
        )
        self.title_entry = ctk.CTkEntry(form, width=300)
        self.title_entry.grid(row=0, column=1, padx=10, pady=(10, 0), sticky="ew")

        # Описание
        ctk.CTkLabel(form, text="Описание:", font=ctk.CTkFont(weight="bold")).grid(
            row=1, column=0, padx=10, pady=(10, 0), sticky="w"
        )
        self.desc_entry = ctk.CTkEntry(form, width=300)
        self.desc_entry.grid(row=1, column=1, padx=10, pady=(10, 0), sticky="ew")

        # Чекбокс дедлайна
        self.deadline_enabled = ctk.IntVar(value=0)
        ctk.CTkCheckBox(
            form, text="Установить дедлайн", variable=self.deadline_enabled,
            command=self._toggle_deadline_widgets
        ).grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")

        # Виджеты выбора дедлайна
        self.deadline_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.deadline_frame.grid(row=3, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew")
        self.deadline_frame.grid_remove()
        
        self._build_deadline_widgets()
        
        # Значения по умолчанию
        tomorrow = date.today() + timedelta(days=1)
        if self.calendar:
            self.calendar.set_date(tomorrow)
        if self.hour_entry:
            self.hour_entry.insert(0, "00")
        if self.minute_entry:
            self.minute_entry.insert(0, "00")

        # Кнопка добавления
        ctk.CTkButton(
            form, text="➕ Добавить задачу", command=self.add_task, height=35
        ).grid(row=4, column=0, columnspan=2, pady=15)
        
        form.columnconfigure(1, weight=1)

    def _build_deadline_widgets(self) -> None:
        """Простое создание виджетов даты и времени."""
        self.calendar = DateEntry(
            self.deadline_frame, width=12, date_pattern='yyyy-mm-dd',
            background='darkblue', foreground='white', borderwidth=2
        )
        self.calendar.pack(side="left", padx=(0, 10))
        
        time_frame = ctk.CTkFrame(self.deadline_frame, fg_color="transparent")
        time_frame.pack(side="left")
        
        self.hour_entry = ctk.CTkEntry(time_frame, width=40)
        self.hour_entry.pack(side="left")
        ctk.CTkLabel(time_frame, text=" : ").pack(side="left")
        self.minute_entry = ctk.CTkEntry(time_frame, width=40)
        self.minute_entry.pack(side="left")
        
        # Дефолт: завтра, 09:00
        tomorrow = date.today() + timedelta(days=1)
        self.calendar.set_date(tomorrow)
        self.hour_entry.insert(0, "09")
        self.minute_entry.insert(0, "00")

    def _toggle_deadline_widgets(self) -> None:
        """Показывает/скрывает виджеты выбора дедлайна."""
        if self.deadline_enabled and self.deadline_frame:
            if self.deadline_enabled.get():
                self.deadline_frame.grid()
            else:
                self.deadline_frame.grid_remove()

    def _build_tasks_list(self) -> None:
        """Создает контейнер для списка задач."""
        self.tasks_container = ctk.CTkScrollableFrame(
            self.main_frame, label_text="Мои задачи"
        )
        self.tasks_container.pack(fill="both", expand=True, pady=0)

    def refresh(self) -> None:
        """Обновляет список задач."""
        if not self.tasks_container:
            return
            
        # Очистка
        for widget in self.tasks_container.winfo_children():
            widget.destroy()
            
        tasks = self.task_manager.get_all_tasks(self.user_id)
        
        if not tasks:
            ctk.CTkLabel(
                self.tasks_container, text="✨ У вас пока нет задач. Добавьте первую!",
                font=ctk.CTkFont(size=14)
            ).pack(pady=30)
            return
            
        for task in tasks:
            TaskCard(
                parent=self.tasks_container,
                task=task,
                on_toggle=self.toggle_task,
                on_edit=self.edit_deadline,
                on_delete=self.delete_task
            )

    def _parse_deadline(self) -> datetime | None:
        """Парсит дату и время из виджетов формы."""
        if not (self.deadline_enabled and self.deadline_enabled.get()):
            return None
        if not (self.calendar and self.hour_entry and self.minute_entry):
            return None
            
        try:
            date_str = self.calendar.get()
            hours = int(self.hour_entry.get().strip())
            minutes = int(self.minute_entry.get().strip())
            
            if not (0 <= hours <= 23) or not (0 <= minutes <= 59):
                raise ValueError("Некорректное время")
                
            return datetime.strptime(
                f"{date_str} {hours:02d}:{minutes:02d}", 
                "%Y-%m-%d %H:%M"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Неверный дедлайн: {e}")
            return None

    def add_task(self) -> None:
        """Добавление задачи с простой и надёжной проверкой дедлайна."""
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()
        
        if not title:
            messagebox.showerror("Ошибка", "Название задачи не может быть пустым.")
            return
        
        deadline = None
        if self.deadline_enabled.get():
            try:
                # calendar.get() может вернуть строку или date, приводим к строке
                date_str = str(self.calendar.get())
                h = int(self.hour_entry.get().strip() or 0)
                m = int(self.minute_entry.get().strip() or 0)
                
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError("Время должно быть от 00:00 до 23:59")
                    
                deadline = datetime.strptime(f"{date_str} {h:02d}:{m:02d}", "%Y-%m-%d %H:%M")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверный формат даты или времени: {e}")
                return
        
        try:
            self.app.task_manager.add_task(self.app.current_user.id, title, description, deadline)
            self._reset_form()
            self.app.refresh_tasks()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить задачу: {e}")

    def _reset_form(self) -> None:
        """Сбрасывает форму добавления задачи к значениям по умолчанию."""
        if self.title_entry:
            self.title_entry.delete(0, 'end')
        if self.desc_entry:
            self.desc_entry.delete(0, 'end')
        if self.deadline_enabled:
            self.deadline_enabled.set(0)
            self._toggle_deadline_widgets()
        if self.calendar:
            self.calendar.set_date(date.today() + timedelta(days=1))
        if self.hour_entry:
            self.hour_entry.delete(0, 'end')
            self.hour_entry.insert(0, "00")
        if self.minute_entry:
            self.minute_entry.delete(0, 'end')
            self.minute_entry.insert(0, "00")

    def toggle_task(self, task: Task) -> None:
        """Переключает статус выполнения задачи."""
        try:
            if self.task_manager.toggle_completed(self.user_id, task.id):
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось изменить статус задачи.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить статус: {e}")

    def delete_task(self, task: Task) -> None:
        """Удаляет задачу."""
        try:
            if self.task_manager.delete_task(self.user_id, task.id):
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Задача не найдена или принадлежит другому пользователю.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    def edit_deadline(self, task: Task) -> None:
        """Открывает диалог редактирования дедлайна."""
        def on_save(task_id: int, deadline: datetime | None):
            if self.task_manager.update_deadline(task_id, deadline):
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить дедлайн")
                
        DeadlineEditDialog(self.root, task, on_save)