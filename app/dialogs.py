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

        def build_datetime_widgets(self) -> None:
            """Простое создание виджетов для диалога."""
            self.calendar = DateEntry(
                self.deadline_frame, width=12, date_pattern='yyyy-mm-dd',
                borderwidth=2
            )
            self.calendar.pack(side="left", padx=(0, 10))
            
            time_frame = ctk.CTkFrame(self.deadline_frame, fg_color="transparent")
            time_frame.pack(side="left")
            
            self.hour_entry = ctk.CTkEntry(time_frame, width=40)
            self.hour_entry.pack(side="left")
            ctk.CTkLabel(time_frame, text=" : ").pack(side="left")
            self.minute_entry = ctk.CTkEntry(time_frame, width=40)
            self.minute_entry.pack(side="left")
            
            if self.task.deadline:
                self.calendar.set_date(self.task.deadline.date())
                self.hour_entry.insert(0, f"{self.task.deadline.hour:02d}")
                self.minute_entry.insert(0, f"{self.task.deadline.minute:02d}")
            else:
                tomorrow = date.today() + timedelta(days=1)
                self.calendar.set_date(tomorrow)
                self.hour_entry.insert(0, "09")
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
        """Сохранение с простой проверкой введённых данных."""
        new_deadline = None
        
        if self.deadline_enabled.get():
            try:
                date_str = str(self.calendar.get())
                h = int(self.hour_entry.get().strip() or 0)
                m = int(self.minute_entry.get().strip() or 0)
                
                if not (0 <= h <= 23 and 0 <= m <= 59):
                    raise ValueError("Время должно быть от 00:00 до 23:59")
                    
                new_deadline = datetime.strptime(f"{date_str} {h:02d}:{m:02d}", "%Y-%m-%d %H:%M")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Неверный формат даты или времени: {e}")
                return
                
        self._on_save(self.task.id, new_deadline)
        self.destroy()