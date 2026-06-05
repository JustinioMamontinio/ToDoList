"""Диалоговые окна приложения."""
import customtkinter as ctk
from tkinter import messagebox
from tkcalendar import DateEntry
from datetime import datetime, date, timedelta
from models import Task
from .helpers import center_window


class DeadlineEditDialog(ctk.CTkToplevel):
    """Диалог редактирования дедлайна задачи."""
    
    def __init__(
        self,
        master: ctk.CTk,
        task: Task,
        on_save: callable
    ):
        super().__init__(master)
        self.task = task
        self._on_save = on_save
        self._configure_window()
        self._build_ui()

    def _configure_window(self) -> None:
        """Настройка параметров окна."""
        self.title("Изменить дедлайн")
        self.geometry("450x250")
        self.transient(self.master)
        self.grab_set()
        center_window(self, 450, 250)
        self.resizable(False, False)

    def _build_ui(self) -> None:
        """Создает элементы интерфейса диалога."""
        # Заголовок
        ctk.CTkLabel(
            self, text="Настройка дедлайна",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(pady=10)

        # Чекбокс включения дедлайна
        self.deadline_enabled = ctk.IntVar(value=1 if self.task.deadline else 0)
        check = ctk.CTkCheckBox(
            self, text="Установить дедлайн",
            variable=self.deadline_enabled, command=self._toggle_widgets
        )
        check.pack(anchor="w", padx=20, pady=5)

        # Контейнер для виджетов выбора даты/времени
        self.deadline_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._build_datetime_widgets()
        
        # Кнопки
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=20)
        ctk.CTkButton(btn_frame, text="Сохранить", command=self._save).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.destroy).pack(side="left", padx=10)

        # Инициализация видимости
        self._toggle_widgets()

    def _build_datetime_widgets(self) -> None:
        """Создает виджеты выбора даты и времени."""
        # Календарь
        self.calendar = DateEntry(
            self.deadline_frame, width=12, date_pattern='yyyy-mm-dd'
        )
        self.calendar.pack(side="left", padx=(0, 10))

        # Время
        time_frame = ctk.CTkFrame(self.deadline_frame, fg_color="transparent")
        time_frame.pack(side="left")
        
        self.hour_entry = ctk.CTkEntry(time_frame, width=40)
        self.hour_entry.pack(side="left")
        ctk.CTkLabel(time_frame, text=" : ").pack(side="left")
        self.minute_entry = ctk.CTkEntry(time_frame, width=40)
        self.minute_entry.pack(side="left")

        # Заполнение значениями
        if self.task.deadline:
            self.calendar.set_date(self.task.deadline.date())
            self.hour_entry.insert(0, f"{self.task.deadline.hour:02d}")
            self.minute_entry.insert(0, f"{self.task.deadline.minute:02d}")
        else:
            tomorrow = date.today() + timedelta(days=1)
            self.calendar.set_date(tomorrow)
            self.hour_entry.insert(0, "00")
            self.minute_entry.insert(0, "00")

    def _toggle_widgets(self) -> None:
        """Показывает/скрывает виджеты выбора даты."""
        if self.deadline_enabled.get():
            self.deadline_frame.pack(fill="x", padx=20, pady=10)
        else:
            self.deadline_frame.pack_forget()

    def _parse_datetime(self) -> datetime | None:
        """Парсит введенные дату и время."""
        if not self.deadline_enabled.get():
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

    def _save(self) -> None:
        """Обработчик кнопки сохранения."""
        new_deadline = self._parse_datetime()
        if new_deadline is None and self.deadline_enabled.get():
            return  # Ошибка валидации уже показана
        if self.deadline_enabled.get() and new_deadline is None:
            return
            
        self._on_save(self.task.id, new_deadline)
        self.destroy()