from datetime import datetime, timedelta
from typing import List

from sqlalchemy.orm import Session

from app.db.models import Game, Notification, User, NotificationReceiver


class NotificationService:
    @staticmethod
    def create_notification(
        db: Session, game_id: int, text: str
    ) -> Notification:
        if not text.strip():
            raise ValueError("Текст уведомления не может быть пустым")

        game = db.get(Game, game_id)
        if not game:
            raise ValueError("Игра не найдена")

        notification = Notification(game_id=game_id, text=text)

        db.add(notification)
        db.commit()
        db.refresh(notification)

        return notification

    @staticmethod
    def send_notification_to_users(db: Session, user_ids: List[int], notification: Notification) -> List[NotificationReceiver]:
        receivers = [NotificationReceiver(
            notification_id=notification.id,
            user_id=user_id
        ) for user_id in user_ids]
        db.add_all(receivers)
        db.commit()
        db.refresh(receivers)
        return receivers

    @staticmethod
    def cleanup_old_notifications(db: Session, days_to_keep: int = 30) -> None:
        threshold_date = datetime.now() - timedelta(days=days_to_keep)
        db.query(NotificationReceiver).filter(
            NotificationReceiver.is_read == True,
            NotificationReceiver.read_at < threshold_date
        ).delete(synchronize_session=False)
        db.commit()
