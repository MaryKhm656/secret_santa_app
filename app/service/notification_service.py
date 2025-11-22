from typing import List

from sqlalchemy.orm import Session

from app.db.models import Game, Notification, NotificationReceiver, User


class NotificationService:
    @staticmethod
    def create_notification(db: Session, game_id: int, text: str) -> Notification:
        """Creates the notification itself (without assigning recipients)"""
        notification = Notification(game_id=game_id, text=text)
        db.add(notification)
        db.commit()
        db.refresh(notification)
        return notification

    @staticmethod
    def send_notification_to_users(
        db: Session, user_ids: List[int], notification: Notification
    ) -> List[NotificationReceiver]:
        """Creates notification associations with specific recipients"""
        receivers = [
            NotificationReceiver(notification_id=notification.id, user_id=user_id)
            for user_id in user_ids
        ]
        db.add_all(receivers)
        db.commit()
        return receivers
