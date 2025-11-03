from sqlalchemy.orm import Session

from app.constants import JoinRequestStatus
from app.db.models import Game, JoinRequest, User


class JoinRequestService:
    @staticmethod
    def create_join_request(
        db: Session, user_id: int, game_id: int, organizer_id: int
    ) -> JoinRequest:
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
