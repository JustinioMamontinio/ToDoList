"""Утилиты для работы с путями и данными пользователя."""
import sys
import os


def user_data_path(filename: str) -> str:
    """
    Возвращает абсолютный путь к файлу в директории приложения.
    
    Args:
        filename: Имя файла относительно корня приложения.
    
    Returns:
        Полный путь к файлу.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, filename)