"""Модуль интерфейса авторизации и регистрации."""
import customtkinter as ctk
from tkinter import messagebox
from sqlalchemy.exc import IntegrityError
from auth import AuthService
from models import User

from email_validator import validate_email, EmailNotValidError


class AuthView:
    """Управление экранами входа и регистрации."""
    
    def __init__(
        self,
        main_frame: ctk.CTkFrame,
        root: ctk.CTk,
        auth_service: AuthService,
        on_login_success: callable,
        on_show_tasks: callable
    ):
        self.main_frame = main_frame
        self.root = root
        self.auth_service = auth_service
        self._on_login_success = on_login_success
        self._on_show_tasks = on_show_tasks
        
        # Виджеты формы входа
        self.login_email: ctk.CTkEntry | None = None
        self.login_password: ctk.CTkEntry | None = None
        
        # Виджеты формы регистрации
        self.reg_email: ctk.CTkEntry | None = None
        self.nickname:ctk.CTkEntry | None = None
        self.reg_password: ctk.CTkEntry | None = None
        self.reg_confirm: ctk.CTkEntry | None = None

    def clear_frame(self) -> None:
        """Очищает основной фрейм от всех виджетов."""
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_login(self) -> None:
        """Отображает форму входа."""
        self.clear_frame()
        self.root.geometry("400x400")
        self.root.resizable(False, False)

        ctk.CTkLabel(
            self.main_frame, text="Добро пожаловать!",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=20)

        # Email
        ctk.CTkLabel(self.main_frame, text="Email:").pack(pady=(10, 0))
        self.login_email = ctk.CTkEntry(self.main_frame, width=300)
        self.login_email.pack(padx = 5, pady=5)

        # Пароль
        ctk.CTkLabel(self.main_frame, text="Пароль:").pack(pady=(10, 0))
        self.login_password = ctk.CTkEntry(self.main_frame, show="*", width=300)
        self.login_password.pack(padx = 5, pady=5)

        # Кнопки
        ctk.CTkButton(self.main_frame, text="Войти", command=self.do_login, width=120).pack(side="left", padx=37.5)
        ctk.CTkButton(self.main_frame, text="Регистрация", command=self.show_register, width=120).pack(side="left", padx=5)

        if self.login_email:
            self.login_email.focus()
        self.root.bind('<Return>', lambda e: self.do_login())

    def show_register(self) -> None:
        """Отображает форму регистрации."""
        self.clear_frame()
        self.root.geometry("400x500")
        self.root.resizable(False, False)

        ctk.CTkLabel(
            self.main_frame, text="Создание аккаунта",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=15)

        #Никнейм
        ctk.CTkLabel(self.main_frame, text="Отображаемое имя:").pack(anchor = 'w', padx = 30, pady=(10,0))
        self.nickname = ctk.CTkEntry(self.main_frame, width=300)
        self.nickname.pack(padx = 2, pady = 5)

        # Email
        ctk.CTkLabel(self.main_frame, text="Email:").pack(anchor = 'w', padx = 30, pady=(10, 0))
        self.reg_email = ctk.CTkEntry(self.main_frame, width=300)
        self.reg_email.pack(padx = 2, pady=5)

        # Пароль
        ctk.CTkLabel(self.main_frame, text="Пароль:").pack(anchor = 'w', padx = 30, pady=(10, 0))
        self.reg_password = ctk.CTkEntry(self.main_frame, show="*", width=300)
        self.reg_password.pack(padx = 2, pady=5)

        # Подтверждение пароля
        ctk.CTkLabel(self.main_frame, text="Подтверждение пароля:").pack(anchor = 'w', padx = 30, pady=(10, 0))
        self.reg_confirm = ctk.CTkEntry(self.main_frame, show="*", width=300)
        self.reg_confirm.pack(padx = 2, pady=5)

        # Кнопки
        ctk.CTkButton(self.main_frame, text="Зарегистрироваться", command=self.do_register).pack(side="left", padx=20)
        ctk.CTkButton(self.main_frame, text="Назад", command=self.show_login).pack(side="left", padx=15)

        if self.nickname:
            self.nickname.focus()

    def do_login(self) -> None:
        """Обрабатывает попытку входа."""
        if not self.login_email or not self.login_password:
            return
            
        email = self.login_email.get().strip()
        password = self.login_password.get()
        
        if not email or not password:
            messagebox.showerror("Ошибка", "Введите email и пароль.")
            return
            
        user = self.auth_service.login(email, password)
        if user:
            self._on_login_success(user, email)
            self._on_show_tasks()
        else:
            messagebox.showerror("Ошибка", "Неверный email или пароль.")

    def do_register(self) -> None:
        """Обрабатывает попытку регистрации."""
        if not self.reg_email or not self.reg_password or not self.reg_confirm:
            return
            
        email = self.reg_email.get().strip()
        nickname = self.nickname.get()
        password = self.reg_password.get()
        confirm = self.reg_confirm.get()
        
        if not email or not password or not nickname:
            messagebox.showerror("Ошибка", "Заполните все поля.")
            return
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают.")
            return
        if not self.check_email(email):
            return
        
        try:
            user = self.auth_service.register(email, nickname, password)
            if user:
                messagebox.showinfo("Успех", f"Регистрация прошла успешно, {nickname}!")
                self.show_login()
        except IntegrityError:
            self.auth_service.session.rollback()
            messagebox.showerror("Ошибка", "Пользователь с таким email уже существует.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {e}")

    def check_email(self, email):
        try:
            v = validate_email(email)
            res_email = v['email']
            return res_email
        except EmailNotValidError as e:
            print(str(e))
            messagebox.showerror("Ошибка", "Введен некорректный email.")
            return None