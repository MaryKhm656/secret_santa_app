from typing import List

from sqlalchemy.orm import Session

from app.constants import JoinRequestStatus, NotificationsData
from app.db.models import Game, JoinRequest, User
from app.schemas.join_requests import JoinResult
from app.service.notification_service import NotificationService
from app.service.participant_service import ParticipantService


class JoinRequestService:
    @staticmethod
    def create_join_request(
        db: Session, user_id: int, game_id: int, organizer_id: int
    ) -> JoinRequest:
        if user_id == organizer_id:
            raise ValueError(
                "Вы являетесь организатором игры и не можете "
                "отправить запрос на вступление."
            )

        user = db.get(User, user_id)
        if not user:
            raise ValueError("Пользователь не найден")

        game = db.get(Game, game_id)
        if not game:
            raise ValueError("Игра не найдена")

        join_request = JoinRequest(
            user_id=user_id, game_id=game_id, organizer_id=organizer_id
        )

        db.add(join_request)
        db.commit()
        db.refresh(join_request)

        return join_request

    @staticmethod
    def update_join_request_status(
        db: Session, new_status: str, join_request_id: int
    ) -> JoinRequest:
        join_request = db.get(JoinRequest, join_request_id)
        if not join_request:
            raise ValueError("Запрос не найден")

        if new_status not in JoinRequestStatus.ALL:
            raise ValueError("Недопустимый статус запроса")

        join_request.status = new_status

        db.commit()
        db.refresh(join_request)

        return join_request

    @staticmethod
    def get_user_join_requests(db: Session, user_id: int) -> List[JoinRequest]:
        return (
            db.query(JoinRequest)
            .filter(JoinRequest.user_id == user_id)
            .order_by(JoinRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def get_pending_requests_for_organizer(
        db: Session, organizer_id: int
    ) -> List[JoinRequest]:
        return (
            db.query(JoinRequest)
            .filter(
                JoinRequest.organizer_id == organizer_id,
                JoinRequest.status == JoinRequestStatus.PENDING,
            )
            .order_by(JoinRequest.created_at.desc())
            .all()
        )

    @staticmethod
    def approve_join_request(
        db: Session, request_id: int, organizer_id: int
    ) -> JoinResult:
        join_request = (
            db.query(JoinRequest)
            .filter(
                JoinRequest.id == request_id,
                JoinRequest.organizer_id == organizer_id,
                JoinRequest.status == JoinRequestStatus.PENDING,
            )
            .first()
        )

        if not join_request:
            raise ValueError("Заявка не найдена или уже обработана")

        join_request.status = JoinRequestStatus.APPROVED

        participant = ParticipantService.create_participant(
            db, join_request.user_id, join_request.game_id
        )

        notification = NotificationService.create_notification(
            db, join_request.game_id, NotificationsData.ACCEPT_JOIN_REQUEST
        )

        receiver = NotificationService.send_notification_to_users(
            db, [join_request.user_id], notification
        )

        db.commit()

        return JoinResult(
            participant=participant,
            receivers=receiver,
            notification=notification,
            join_request=join_request,
        )

    @staticmethod
    def reject_join_request(
        db: Session, request_id: int, organizer_id: int
    ) -> JoinRequest:
        join_request = (
            db.query(JoinRequest)
            .filter(
                JoinRequest.id == request_id,
                JoinRequest.organizer_id == organizer_id,
                JoinRequest.status == JoinRequestStatus.PENDING,
            )
            .first()
        )

        if not join_request:
            raise ValueError("Заявка не найдена или уже обработана")

        join_request.status = JoinRequestStatus.REJECTED
        db.commit()
        db.refresh(join_request)

        return join_request
