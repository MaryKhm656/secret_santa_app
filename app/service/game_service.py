from datetime import datetime
from typing import Optional, Union

from sqlalchemy.orm import Session

from app.constants import JoinRequestStatus, NotificationsData, GameStatus
from app.db.models import Game, JoinRequest, Participant, User
from app.schemas.games import GameCreateData, GameUpdateData
from app.schemas.join_requests import JoinResult
from app.service.join_requset_service import JoinRequestService
from app.service.notification_service import NotificationService
from app.service.participant_service import ParticipantService


class GameService:
    @staticmethod
    def _validate_event_date(event_date: Union[datetime, str]) -> Optional[datetime]:
        """Validates and converts event date of game"""
        if isinstance(event_date, str):
            if not event_date.strip():
                event_date = None
            else:
                try:
                    event_date = datetime.strptime(event_date, "%Y-%m-%d %H:%M")
                except ValueError:
                    raise ValueError(
                        "Неверный формат даты. Ожидается формат: 'YYYY-MM-DD HH:MM'"
                    )

        if event_date and event_date < datetime.now():
            raise ValueError("Нельзя установить дату проведения игры в прошлом")

        return event_date

    @staticmethod
    def create_game(db: Session, game_data: GameCreateData) -> Game:
        """Method for creating game model in DB"""
        if len(game_data.title.strip()) < 2:
            raise ValueError("Слишком короткое название игры")

        game_data.event_date = GameService._validate_event_date(game_data.event_date)

        if game_data.budget and game_data.budget < 0:
            raise ValueError("Бюджет игры не может быть отрицательным")

        user = db.get(User, game_data.organizer_id)
        if not user:
            raise ValueError("Организатор с таким ID не найден")

        game = Game(
            title=game_data.title.strip(),
            description=game_data.description,
            budget=game_data.budget,
            event_date=game_data.event_date,
            secret_key=game_data.secret_key,
            organizer_id=game_data.organizer_id,
            is_private=game_data.is_private,
            status=game_data.status.lower().strip()
        )
        db.add(game)
        db.commit()
        db.refresh(game)

        return game

    @staticmethod
    def find_game_by_secret_key(db: Session, secret_key: str) -> Optional[Game]:
        return db.query(Game).filter(Game.secret_key==secret_key).first()

    @staticmethod
    def join_the_game(db: Session, user_id: int, secret_key: str) -> JoinResult:
        game = GameService.find_game_by_secret_key(db, secret_key)
        if not game:
            raise ValueError("Игра по такому секретному ключу не найдена")

        existing_participant = (
            db.query(Participant).filter_by(user_id=user_id, game_id=game.id).first()
        )
        if existing_participant:
            raise ValueError("Вы уже участвуете в этой игре")

        existing_request = (
            db.query(JoinRequest)
            .filter_by(
                user_id=user_id, game_id=game.id, status=JoinRequestStatus.PENDING
            )
            .first()
        )
        if existing_request:
            raise ValueError("Вы уже подали заявку на вступление в эту игру")

        if game.is_private:
            join_request = JoinRequestService.create_join_request(
                db, user_id, game.id, game.organizer_id
            )
            notification_for_user = NotificationService.create_notification(
                db, user_id, game.id, text=NotificationsData.JOIN_REQUEST_HAS_BEEN_SEND
            )
            notification_for_organizer = NotificationService.create_notification(
                db, game.organizer_id, game.id, NotificationsData.NEW_JOIN_REQUEST
            )
            return JoinResult(
                join_request=join_request,
                notifications=[notification_for_user, notification_for_organizer],
            )
        else:
            participant = ParticipantService.create_participant(db, user_id, game.id)
            notification = NotificationService.create_notification(
                db,
                game.organizer_id,
                game.id,
                NotificationsData.NEW_PARTICIPANT_IN_GAME,
            )
            return JoinResult(participant=participant, notifications=[notification])

    @staticmethod
    def join_the_game_after_accept_request(
        db: Session, user_id: int, join_request: JoinRequest
    ) -> JoinResult:
        if join_request.status == JoinRequestStatus.APPROVED:
            participant = ParticipantService.create_participant(
                db, user_id, join_request.game_id
            )
            notification = NotificationService.create_notification(
                db, user_id, join_request.game_id, NotificationsData.ACCEPT_JOIN_REQUEST
            )
            join_result = JoinResult(
                participant=participant,
                notifications=[notification]
            )
            return join_result
        elif join_request.status == JoinRequestStatus.PENDING:
            raise ValueError("Организатор ещё не принял ваш запрос. Чуточку терпения!")
        else:
            raise ValueError("Организатор отклонил ваш запрос на вступление в игру!")

    @staticmethod
    def update_game_data(db: Session, game_id: int, new_game_data: GameUpdateData, organizer_id: int) -> Game:
        game = db.get(Game, game_id)
        if not game:
            raise ValueError("Игра не найдена!")

        if game.organizer_id != organizer_id:
            raise ValueError("Данные действия доступны только организатору игры")

        if new_game_data.title:
            if len(new_game_data.title.strip()) < 2:
                raise ValueError("Слишком короткое название игры")
            game.title = new_game_data.title.strip()

        if new_game_data.is_private:
            game.is_private = new_game_data.is_private

        if new_game_data.secret_key:
            game.secret_key = new_game_data.secret_key

        if new_game_data.description:
            game.description = new_game_data.description

        if new_game_data.budget:
            if new_game_data.budget < 0:
                raise ValueError("Бюджет игры не может быть отрицательным")
            game.budget = new_game_data.budget

        if new_game_data.event_date:
            new_game_data.event_date = GameService._validate_event_date(new_game_data.event_date)
            game.event_date = new_game_data.event_date

        if new_game_data.status:
            if new_game_data.status.lower().strip() not in GameStatus.ALL:
                raise ValueError("Недопустимый статус игры")
            game.status = new_game_data.status.lower().strip()

        return game
