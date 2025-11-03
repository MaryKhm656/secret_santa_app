from sqlalchemy.orm import Session

from app.db.models import Game, Notification, User


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session, user_id: int, game_id: int, text: str
    ) -> Notification:
        if not text.strip():
            raise ValueError("Текст уведомления не может быть пустым")

        user = db.get(User, user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        game = db.get(Game, game_id)
        if not game:
            raise ValueError("Игра не найдена")

        notification = Notification(user_id=user_id, game_id=game_id, text=text)

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification
