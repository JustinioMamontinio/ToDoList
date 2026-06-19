"""Виджет карточки группы задач."""
import customtkinter as ctk
import tkinter as tk
from models import GroupTask

class GroupCard(tk.Frame):
    def __init__(
        self,
        parent,
        group: GroupTask,
        level: int,
        on_toggle: callable,
        on_add_task: callable,
        on_add_group: callable,
        on_delete: callable,
        **kwargs
    ):
        super().__init__(parent, bg="#2b2b2b", relief="solid", borderwidth=1, **kwargs)
        self.group = group
        self.level = level
        self._on_toggle = on_toggle
        self._on_add_task = on_add_task
        self._on_add_group = on_add_group
        self._on_delete = on_delete
        
        # Получаем прогресс из @property модели
        done, total = self.group.progress
        self.progress_value = (done / total) if total > 0 else 0.0
        
        self._build_ui()

    def _build_ui(self) -> None:
        # Отступ для вложенности
        indent = self.level * 20
        
        # Верхняя строка: кнопка сворачивания + Название
        top_frame = tk.Frame(self, bg="#2b2b2b")
        top_frame.pack(fill="x", padx=(4 + indent, 8), pady=(4, 2))
        
        # Кнопка развернуть/свернуть (треугольник)
        toggle_btn = tk.Label(
            top_frame, text="▼" if self.group.id in getattr(self.master, 'expanded_groups', set()) else "▶",
            font=("Segoe UI", 10), fg="white", bg="#2b2b2b", cursor="hand2"
        )
        toggle_btn.pack(side="left")
        toggle_btn.bind("<Button-1>", lambda e: self._on_toggle(self.group.id))
        
        # Название группы
        tk.Label(
            top_frame, text=self.group.title,
            font=("Segoe UI", 12, "bold"), fg="#3498db", bg="#2b2b2b"
        ).pack(side="left", padx=5)
        
        # Прогресс текстом
        done, total = self.group.progress
        tk.Label(
            top_frame, text=f"{done}/{total}",
            font=("Segoe UI", 10), fg="gray", bg="#2b2b2b"
        ).pack(side="right")

        # Прогресс-бар (customtkinter)
        progress_bar = ctk.CTkProgressBar(
            self, width=300, height=6, corner_radius=3,
            progress_color="#2ecc71" if self.progress_value == 1.0 else "#3498db"
        )
        progress_bar.pack(fill="x", padx=(24 + indent, 8), pady=(0, 4))
        progress_bar.set(self.progress_value)

        # Кнопки действий (только для развернутой группы или всегда, по желанию)
        btn_frame = tk.Frame(self, bg="#2b2b2b")
        btn_frame.pack(fill="x", padx=(24 + indent, 8), pady=(0, 4))
        
        ctk.CTkButton(
            btn_frame, text="➕ Задача", width=70, height=22, font=("Segoe UI", 9),
            command=lambda: self._on_add_task(self.group.id)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame, text="📁 Подгруппа", width=80, height=22, font=("Segoe UI", 9),
            command=lambda: self._on_add_group(self.group.id)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            btn_frame, text="🗑 Удалить", width=70, height=22, font=("Segoe UI", 9),
            fg_color="#d32f2f", hover_color="#b71c1c",
            command=lambda: self._on_delete(self.group.id)
        ).pack(side="right", padx=2)