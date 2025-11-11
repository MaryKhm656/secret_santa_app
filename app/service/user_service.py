from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import User
from app.schemas.users import UserCreateData, UserUpdateData


class UserService:
    @staticmethod
    def create_user(
        db: Session,
        user_data: UserCreateData,
    ) -> User:
        """Method for create new user in DB"""
        if user_data.username and len(user_data.username.strip()) < 2:
            raise ValueError("Имя пользователя не может быть меньше двух символов")

        if "@" not in user_data.email or "." not in user_data.email:
            raise ValueError("Некорректный email")

        existing_user = (
            db.query(User).filter_by(email=user_data.email, is_deleted=False).first()
        )
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")

        hashed_password = hash_password(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            password_hash=hashed_password,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def update_user_data(
        db: Session, user_id: int, new_user_data: UserUpdateData
    ) -> User:
        user = db.query(User).filter(User.id == user_id).first_not_deleted()
        if not user:
            raise ValueError("Пользователь не найден")

        if user.username != new_user_data.username:
            user.username = new_user_data.username

        if user.email != new_user_data.email:
            if "@" not in new_user_data.email or "." not in new_user_data.email:
                raise ValueError("Некорректный email")
            user.email = new_user_data.email

        if user.wishlist != new_user_data.wishlist:
            user.wishlist = new_user_data.wishlist

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_wishlist(db: Session, user_id: int, wishlist_text: str) -> User:
        user = db.query(User).filter(User.id == user_id).first_not_deleted()
        if not user:
            raise ValueError("Пользователь не найден")

        user.wishlist = wishlist_text

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def delete_user(db: Session, user_id: int) -> Optional[str]:
        user = db.get(User, user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        user.soft_delete()
        db.commit()
        return "Пользователь успешно удален"
