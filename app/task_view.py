"""Модуль интерфейса управления задачами и группами."""

# Стандартная библиотека
from datetime import date, datetime, timedelta

# Сторонние библиотеки
import customtkinter as ctk
from tkcalendar import DateEntry
from tkinter import messagebox

# Локальные модули
from models import GroupTask, Task
from tasks import TaskManager, GroupManager

from .dialogs import DeadlineEditDialog
from .group_card import GroupCard
from .task_card import TaskCard


class TaskView:
    """
    Управление экраном списка задач и групп.

    Отвечает за отображение иерархической структуры задач,
    обработку пользовательского ввода и взаимодействие с менеджерами.
    """

    # Константы оформления
    WINDOW_WIDTH = 950
    WINDOW_HEIGHT = 750
    DEFAULT_HOUR = "09"
    DEFAULT_MINUTE = "00"

    def __init__(
        self,
        main_frame: ctk.CTkFrame,
        root: ctk.CTk,
        task_manager: TaskManager,
        group_manager: GroupManager,
        user_id: int,
        on_logout: callable,
        on_refresh: callable,
    ) -> None:
        """
        Инициализация экрана задач.

        Args:
            main_frame: Родительский фрейм для размещения виджетов.
            root: Корневое окно приложения.
            task_manager: Менеджер для работы с задачами.
            group_manager: Менеджер для работы с группами задач.
            user_id: ID текущего пользователя.
            on_logout: Callback для выхода из аккаунта.
            on_refresh: Callback для обновления данных.
        """
        self.main_frame = main_frame
        self.root = root
        self.task_manager = task_manager
        self.group_manager = group_manager
        self.user_id = user_id
        self._on_logout = on_logout
        self._on_refresh = on_refresh

        # Состояние сворачивания групп (ID развернутых групп)
        self.expanded_groups: set[int] = set()

        # Виджеты формы добавления задачи
        self.title_entry: ctk.CTkEntry | None = None
        self.desc_entry: ctk.CTkEntry | None = None
        self.deadline_enabled: ctk.IntVar | None = None
        self.deadline_frame: ctk.CTkFrame | None = None
        self.calendar: DateEntry | None = None
        self.hour_entry: ctk.CTkEntry | None = None
        self.minute_entry: ctk.CTkEntry | None = None
        self.tasks_container: ctk.CTkScrollableFrame | None = None

        # Индикатор активной группы и её ID
        self.group_indicator: ctk.CTkLabel | None = None
        self._active_group_id: int | None = None

    def show(self) -> None:
        """Отображает экран управления задачами."""
        self._clear_main_frame()
        self._configure_window()

        self._build_header()
        self._build_add_task_form()
        self._build_tasks_list()
        self.refresh()

        if self.title_entry:
            self.title_entry.focus()
        self.root.bind("<Return>", lambda e: self.add_task())

    def refresh(self) -> None:
        """Обновляет список групп и задач."""
        if not self.tasks_container:
            return

        self._clear_tasks_container()

        root_groups = self.group_manager.get_root_groups(self.user_id)
        ungrouped_tasks = self.task_manager.get_ungrouped_tasks(self.user_id)

        if not root_groups and not ungrouped_tasks:
            self._show_empty_state()
            return

        for group in root_groups:
            self._render_group_recursive(group, level=0)

        for task in ungrouped_tasks:
            TaskCard(
                parent=self.tasks_container,
                task=task,
                level=0,
                on_toggle=self.toggle_task,
                on_edit=self.edit_deadline,
                on_delete=self.delete_task,
            ).pack(fill="x", padx=5, pady=2)

    def add_task(self) -> None:
        """Добавление задачи (в активную группу или в общий список)."""
        title = self.title_entry.get().strip()
        description = self.desc_entry.get().strip()

        if not title:
            messagebox.showerror("Ошибка", "Название задачи не может быть пустым.")
            return

        deadline = self._parse_deadline()
        if deadline is None and self.deadline_enabled.get():
            return

        try:
            if self._active_group_id is not None:
                # Добавляем в группу через GroupManager
                self.group_manager.add_subtask(
                    user_id=self.user_id,
                    group_id=self._active_group_id,
                    title=title,
                    description=description,
                    deadline=deadline,
                )
                self.expanded_groups.add(self._active_group_id)
            else:
                # Обычная задача через TaskManager
                self.task_manager.add_task(
                    self.user_id, title, description, deadline
                )

            self._reset_form()
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить задачу: {e}")

    def toggle_task(self, task: Task) -> None:
        """Переключает статус выполнения задачи."""
        try:
            if self.task_manager.toggle_completed(self.user_id, task.id):
                self.refresh()
            else:
                messagebox.showerror(
                    "Ошибка", "Не удалось изменить статус задачи."
                )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить статус: {e}")

    def delete_task(self, task: Task) -> None:
        """Удаляет задачу."""
        try:
            if self.task_manager.delete_task(self.user_id, task.id):
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Задача не найдена.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    def edit_deadline(self, task: Task) -> None:
        """Открывает диалог редактирования дедлайна."""

        def on_save(task_id: int, deadline: datetime | None) -> None:
            if self.task_manager.update_deadline(task_id, deadline):
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось обновить дедлайн")

        DeadlineEditDialog(self.root, task, on_save)

    def _build_header(self) -> None:
        """Создает заголовок с приветствием и кнопками управления."""
        header = ctk.CTkFrame(self.main_frame, height=50)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text=f"Привет, {self.user_id}!",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            header,
            text="📁 Новая группа",
            command=self._prompt_add_root_group,
            width=120,
        ).pack(side="right", padx=10)

        ctk.CTkButton(
            header, text="Выйти", command=self._on_logout, width=80
        ).pack(side="right", padx=10)

    def _build_add_task_form(self) -> None:
        """Создает форму добавления новой задачи."""
        form = ctk.CTkFrame(self.main_frame, corner_radius=10)
        form.pack(fill="x", pady=10)

        # Индикатор активной группы
        self.group_indicator = ctk.CTkLabel(
            form,
            text="Задача будет добавлена в общий список",
            font=ctk.CTkFont(size=11),
            text_color="#3498db",
        )
        self.group_indicator.grid(
            row=0, column=0, columnspan=2, padx=10, pady=(10, 0), sticky="w"
        )

        # Поле названия
        ctk.CTkLabel(
            form, text="Название:", font=ctk.CTkFont(weight="bold")
        ).grid(row=1, column=0, padx=10, pady=(10, 0), sticky="w")
        self.title_entry = ctk.CTkEntry(form, width=300)
        self.title_entry.grid(
            row=1, column=1, padx=10, pady=(10, 0), sticky="ew"
        )

        # Поле описания
        ctk.CTkLabel(
            form, text="Описание:", font=ctk.CTkFont(weight="bold")
        ).grid(row=2, column=0, padx=10, pady=(10, 0), sticky="w")
        self.desc_entry = ctk.CTkEntry(form, width=300)
        self.desc_entry.grid(
            row=2, column=1, padx=10, pady=(10, 0), sticky="ew"
        )

        # Чекбокс дедлайна
        self.deadline_enabled = ctk.IntVar(value=0)
        ctk.CTkCheckBox(
            form,
            text="Установить дедлайн",
            variable=self.deadline_enabled,
            command=self._toggle_deadline_widgets,
        ).grid(row=3, column=0, padx=10, pady=(10, 0), sticky="w")

        # Виджеты выбора даты и времени
        self.deadline_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.deadline_frame.grid(
            row=4, column=0, columnspan=2, padx=10, pady=(5, 0), sticky="ew"
        )
        self.deadline_frame.grid_remove()
        self._build_deadline_widgets()

        # Кнопка добавления (БЕЗ кнопки "Отмена группы")
        ctk.CTkButton(
            form,
            text="➕ Добавить задачу",
            command=self.add_task,
            height=35,
        ).grid(row=5, column=0, columnspan=2, pady=15)

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

    def _reset_deadline_default(self):
        if self.calendar:
            self.calendar.set_date(date.today() + timedelta(days=1))
        if self.hour_entry:
            self.hour_entry.delete(0, "end")
            self.hour_entry.insert(0, self.DEFAULT_HOUR)
        if self.minute_entry:
            self.minute_entry.delete(0, "end")
            self.minute_entry.insert(0, self.DEFAULT_MINUTE)
    def _build_tasks_list(self) -> None:
        """Создает контейнер для списка задач и групп."""
        self.tasks_container = ctk.CTkScrollableFrame(
            self.main_frame, label_text="Мои задачи"
        )
        self.tasks_container.pack(fill="both", expand=True, pady=0)

    def _render_group_recursive(self, group: GroupTask, level: int) -> None:
        """
        Рекурсивно отрисовывает группу и её содержимое.

        Args:
            group: Группа для отрисовки.
            level: Уровень вложенности (для визуального отступа).
        """
        GroupCard(
            parent=self.tasks_container,
            group=group,
            level=level,
            on_toggle=self._toggle_group,
            on_add_task=self._set_active_group,
            on_add_group=self._prompt_add_subgroup,
            on_delete=self._delete_group,
        ).pack(fill="x", padx=5, pady=2)

        if group.id not in self.expanded_groups:
            return

        for child in group.children:
            self._render_group_recursive(child, level + 1)

        for task in group.tasks:
            TaskCard(
                parent=self.tasks_container,
                task=task,
                level=level + 1,
                on_toggle=self.toggle_task,
                on_edit=self.edit_deadline,
                on_delete=self.delete_task,
            ).pack(fill="x", padx=5, pady=1)

    def _toggle_group(self, group_id: int) -> None:
        """Сворачивает или разворачивает группу."""
        if group_id in self.expanded_groups:
            self.expanded_groups.remove(group_id)
        else:
            self.expanded_groups.add(group_id)
        self.refresh()

    def _prompt_add_root_group(self) -> None:
        """Запрашивает у пользователя название и создаёт корневую группу."""
        self._prompt_add_subgroup(parent_id=None)

    def _prompt_add_subgroup(self, parent_id: int | None) -> None:
        """Запрашивает название и создаёт подгруппу."""
        title = "Новая группа" if parent_id is None else "Новая подгруппа"
        dialog = ctk.CTkInputDialog(
            text="Введите название группы:", title=title
        )
        name = dialog.get_input()

        if not name or not name.strip():
            return

        try:
            self.group_manager.create_group(
                user_id=self.user_id,
                title=name.strip(),
                description="",
                parent_id=parent_id,
            )
            if parent_id is not None:
                self.expanded_groups.add(parent_id)
            self.refresh()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать группу: {e}")

    def _delete_group(self, group_id: int) -> None:
        """Удаляет группу со всеми вложенными элементами."""
        message = (
            "Удалить группу и все вложенные задачи/подгруппы?\n"
            "Это действие нельзя отменить."
        )
        if not messagebox.askyesno("Подтверждение", message):
            return

        try:
            if self.group_manager.delete_group(self.user_id, group_id):
                self.expanded_groups.discard(group_id)
                self.refresh()
            else:
                messagebox.showerror("Ошибка", "Не удалось удалить группу.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления: {e}")

    def _set_active_group(self, group_id: int) -> None:
        """
        Делает группу активной для добавления задач через форму.

        Args:
            group_id: ID группы, в которую будут добавляться задачи.
        """
        self._active_group_id = group_id
        group = self.group_manager.get_group(self.user_id, group_id)

        if self.group_indicator and group:
            self.group_indicator.configure(
                text=f"📁 Задача будет добавлена в группу: {group.title}"
            )
        if self.title_entry:
            self.title_entry.focus()

    def _clear_active_group(self) -> None:
        """Сбрасывает активную группу — новые задачи будут без группы."""
        self._active_group_id = None
        if self.group_indicator:
            self.group_indicator.configure(
                text="Задача будет добавлена в общий список"
            )

    def _parse_deadline(self) -> datetime | None:
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

    def _toggle_deadline_widgets(self) -> None:
        """Показывает или скрывает виджеты выбора дедлайна."""
        if not (self.deadline_enabled and self.deadline_frame):
            return

        if self.deadline_enabled.get():
            self.deadline_frame.grid()
        else:
            self.deadline_frame.grid_remove()

    def _reset_form(self) -> None:
        """Сбрасывает форму добавления задачи к значениям по умолчанию."""
        if self.title_entry:
            self.title_entry.delete(0, "end")
        if self.desc_entry:
            self.desc_entry.delete(0, "end")
        if self.deadline_enabled:
            self.deadline_enabled.set(0)
            self._toggle_deadline_widgets()
        if self.calendar:
            self.calendar.set_date(date.today() + timedelta(days=1))
        if self.hour_entry:
            self.hour_entry.delete(0, "end")
            self.hour_entry.insert(0, "09")
        if self.minute_entry:
            self.minute_entry.delete(0, "end")
            self.minute_entry.insert(0, "00")
            
    def _clear_main_frame(self) -> None:
        """Очищает основной фрейм от всех виджетов."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def _configure_window(self) -> None:
        """Настраивает размер и поведение главного окна."""
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.resizable(True, True)

    def _clear_tasks_container(self) -> None:
        """Очищает контейнер задач от всех виджетов."""
        for widget in self.tasks_container.winfo_children():
            widget.destroy()

    def _show_empty_state(self) -> None:
        """Отображает сообщение при отсутствии задач и групп."""
        ctk.CTkLabel(
            self.tasks_container,
            text="✨ У вас пока нет задач. Создайте первую группу или задачу!",
            font=ctk.CTkFont(size=14),
        ).pack(pady=30)