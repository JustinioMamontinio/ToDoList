"""Сервис аутентификации пользователей."""
import bcrypt
from models import User
from sqlalchemy.orm import Session


class AuthService:
    """Сервис для регистрации и входа пользователей."""
    
    def __init__(self, session: Session):
        self.session = session

    def _hash_password(self, password: str) -> str:
        """Хеширует пароль с использованием bcrypt."""
        return bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')

    def register(self, email: str, nickname: str, password: str) -> User:
        """
        Регистрирует нового пользователя.
        
        Returns:
            Экземпляр созданного пользователя.
        """
        hashed_pw = self._hash_password(password)
        new_user = User(nickname = nickname, email=email, password_hash=hashed_pw)
        self.session.add(new_user)
        self.session.commit()
        return new_user

    def login(self, email: str, password: str) -> User | None:
        """
        Проверяет учетные данные пользователя.
        
        Returns:
            Экземпляр пользователя при успехе, None при ошибке.
        """
        user = self.session.query(User).filter_by(email=email).first()
        if user is None:
            return None
            
        is_valid = bcrypt.checkpw(
            password.encode('utf-8'), 
            user.password_hash.encode('utf-8')
        )
        return user if is_valid else None