"""Виджет карточки отдельной задачи."""
import tkinter as tk
import customtkinter as ctk
from datetime import datetime, timedelta
from models import Task
from .helpers import format_deadline


class TaskCard(tk.Frame):
    """
    Виджет для отображения одной задачи.
    Использует tkinter для карточки и customtkinter для кнопок.
    """
    
    def __init__(
        self,
        parent: tk.Widget,
        task: Task,
        on_toggle: callable,
        on_edit: callable,
        on_delete: callable
    ):
        super().__init__(parent, bg="#2b2b2b", relief="solid", borderwidth=1)
        self.task = task
        self._on_toggle = on_toggle
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._build()

    def _get_status_color(self) -> str:
        """Определяет цвет индикатора слева от карточки."""
        if self.task.is_done:
            return "#2ecc71"
        if not self.task.deadline:
            return "#888888"
        
        now = datetime.now()
        if self.task.deadline < now:
            return "#e74c3c"  # красный - просрочено
        elif (self.task.deadline - now) < timedelta(days=1):
            return "#e67e22"  # оранжевый - скоро
        return "#888888"  # серый - нормально

    def _build(self) -> None:
        """Создает элементы интерфейса карточки."""
        self.pack(fill="x", padx=5, pady=2)
        
        # Цветная полоска-индикатор
        color_bar = tk.Frame(self, bg=self._get_status_color(), width=5)
        color_bar.pack(side="left", fill="y", padx=(4, 8), pady=4)

        # Основной контент
        content = tk.Frame(self, bg="#2b2b2b")
        content.pack(side="left", fill="both", expand=True)

        self._build_header(content)
        self._build_description(content)
        self._build_deadline(content)
        self._build_buttons(content)

    def _build_header(self, parent: tk.Widget) -> None:
        """Строка с названием и статусом."""
        top = tk.Frame(parent, bg="#2b2b2b")
        top.pack(fill="x")
        
        # Название задачи
        title_color = "#888888" if self.task.is_done else "white"
        title_style = ("Segoe UI", 12, "bold" if not self.task.is_done else "normal")
        tk.Label(
            top, text=self.task.title, font=title_style,
            fg=title_color, bg="#2b2b2b"
        ).pack(side="left")
        
        # Статус
        status = "✓ Выполнено" if self.task.is_done else "○ Не выполнено"
        status_color = "#4caf50" if self.task.is_done else "#ff9800"
        tk.Label(
            top, text=status, font=("Segoe UI", 10),
            fg=status_color, bg="#2b2b2b"
        ).pack(side="right")

    def _build_description(self, parent: tk.Widget) -> None:
        """Описание задачи (если есть)."""
        if not self.task.description:
            return
        desc = self.task.description
        if len(desc) > 80:
            desc = desc[:80] + "..."
        tk.Label(
            parent, text=desc, font=("Segoe UI", 11),
            fg="gray", bg="#2b2b2b", anchor="w"
        ).pack(fill="x", pady=(2, 0))

    def _build_deadline(self, parent: tk.Widget) -> None:
        """Информация о дедлайне (если есть)."""
        if not self.task.deadline:
            return
            
        remaining = format_deadline(self.task.deadline)
        deadline_str = self.task.deadline.strftime("%Y-%m-%d %H:%M")
        text = f"📅 {deadline_str} (осталось: {remaining})"
        
        now = datetime.now()
        if self.task.deadline < now:
            color = "#e74c3c"
        elif (self.task.deadline - now) < timedelta(days=1):
            color = "#e67e22"
        else:
            color = "#888888"
            
        tk.Label(
            parent, text=text, font=("Segoe UI", 10),
            fg=color, bg="#2b2b2b"
        ).pack(anchor="w", pady=(2, 0))

    def _build_buttons(self, parent: tk.Widget) -> None:
        """Панель кнопок управления."""
        btn_frame = tk.Frame(parent, bg="#2b2b2b")
        btn_frame.pack(fill="x", pady=(4, 2))

        # Кнопка переключения статуса
        toggle_text = "✅ Выполнить" if not self.task.is_done else "🔄 Отменить"
        ctk.CTkButton(
            btn_frame, text=toggle_text, width=90, height=24,
            command=lambda: self._on_toggle(self.task)
        ).pack(side="left", padx=2)

        # Кнопка редактирования дедлайна
        ctk.CTkButton(
            btn_frame, text="✏ Дедлайн", width=80, height=24,
            command=lambda: self._on_edit(self.task)
        ).pack(side="left", padx=2)

        # Кнопка удаления
        ctk.CTkButton(
            btn_frame, text="🗑 Удалить", width=80, height=24,
            fg_color="#d32f2f", hover_color="#b71c1c",
            command=lambda: self._on_delete(self.task)
        ).pack(side="right", padx=2)