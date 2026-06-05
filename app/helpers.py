"""Вспомогательные функции для GUI."""
import customtkinter as ctk
from datetime import datetime, timedelta


def format_deadline(deadline: datetime | None) -> str:
    """
    Форматирует оставшееся время до дедлайна.
    
    Returns:
        Строка с описанием времени или статусом "Просрочен".
    """
    if not deadline:
        return ""
    
    now = datetime.now()
    if deadline < now:
        return "❗ Просрочен"
    
    delta = deadline - now
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days} д {hours} ч"
    elif hours > 0:
        return f"{hours} ч {minutes} мин"
    return f"{minutes} мин"


def center_window(window: ctk.CTk, width: int, height: int) -> None:
    """Центрирует окно на экране."""
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    window.geometry(f"{width}x{height}+{x}+{y}")


def bring_to_front(window: ctk.CTk) -> None:
    """Поднимает окно на передний план."""
    window.lift()
    window.attributes('-topmost', True)
    window.after(100, lambda: window.attributes('-topmost', False))
    window.focus_force()
    try:
        import ctypes
        ctypes.windll.user32.SetForegroundWindow(window.winfo_id())
    except Exception:
        pass