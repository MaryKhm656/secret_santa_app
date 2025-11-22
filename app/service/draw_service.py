import random
from typing import List, Tuple

from sqlalchemy.orm import Session

from app.constants import NotificationsData
from app.db.models import Draw, DrawAssignment, Game, Participant, User
from app.service.notification_service import NotificationService


class DrawService:
    @staticmethod
    def _generate_assignments(
        participants: List[Participant],
    ) -> List[Tuple[Participant, Participant]]:
        """Generate random gift assignments ensuring no self or reciprocal pairs"""
        for _ in range(100):
            receivers = participants.copy()
            random.shuffle(receivers)
            pairs = list(zip(participants, receivers))

            if any(giver == receiver for giver, receiver in pairs):
                continue

            reciprocal_found = False
            for giver, receiver in pairs:
                if (receiver, giver) in pairs:
                    reciprocal_found = True
                    break

            if reciprocal_found:
                continue

            return pairs

        raise RuntimeError(
            "Не удалось корректно распределить участников после 100 попыток"
        )

    @staticmethod
    def start_draw(db: Session, organizer_id: int, game_id: int) -> Draw:
        """Start gift draw for a game"""
        organizer = db.get(User, organizer_id)
        if not organizer:
            raise ValueError("Пользователь не найден")

        game = db.get(Game, game_id)
        if not game:
            raise ValueError("Игра не найдена")

        if game.organizer_id != organizer.id:
            raise ValueError("Данные действия доступны только организатору игры")

        participants = db.query(Participant).filter_by(game_id=game.id).all()
        if len(participants) < 3:
            raise ValueError("Для жеребьевки нужны минимум 3 участника")

        draw = Draw(game_id=game.id)
        db.add(draw)
        db.flush()

        try:
            assignments = DrawService._generate_assignments(participants)
            for giver, receiver in assignments:
                giver.assigned_to_id = receiver.id
                db.add(giver)
                assignment = DrawAssignment(
                    draw_id=draw.id,
                    participant_from_id=giver.id,
                    participant_to_id=receiver.id,
                )
                db.add(assignment)

            notification = NotificationService.create_notification(
                db, game_id, NotificationsData.DRAW_IS_COMPLETED
            )

            NotificationService.send_notification_to_users(
                db, [giver.user_id for giver, _ in assignments], notification
            )

            db.commit()
        except Exception as e:
            db.rollback()
            raise e

        return draw
