from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import User


class UserService:
    @staticmethod
    def create_user(
        db: Session,
        email: str,
        password: str,
        username: str = None,
    ) -> User:
        """Method for create new user in DB"""
        if username and len(username.strip()) < 2:
            raise ValueError("Имя пользователя не может быть меньше двух символов")

        if "@" not in email or "." not in email:
            raise ValueError("Некорректный email")

        existing_user = db.query(User).filter_by(email=email).first()
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")

        hashed_password = hash_password(password)
        user = User(username=username, email=email, password_hash=hashed_password)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
