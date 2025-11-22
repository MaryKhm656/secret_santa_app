from datetime import datetime
from typing import List, Optional, Union

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.constants import GameStatus, JoinRequestStatus, NotificationsData
from app.db.models import Game, JoinRequest, Participant, User
from app.schemas.games import NOT_PROVIDED, GameCreateData, GameUpdateData
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
            status=game_data.status.lower().strip(),
        )
        db.add(game)
        db.commit()
        db.refresh(game)

        return game

    @staticmethod
    def find_game_by_secret_key(db: Session, secret_key: str) -> Optional[Game]:
        return db.query(Game).filter(Game.secret_key == secret_key).first_not_deleted()

    @staticmethod
    def join_the_game(db: Session, user_id: int, secret_key: str) -> JoinResult:
        """
        A user joins a game:
            - if the game is private → creates a request and notifies the organizer;
            - if the game is public → adds a participant and notifies everyone.
        """

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

            notification = NotificationService.create_notification(
                db=db, game_id=game.id, text=NotificationsData.NEW_JOIN_REQUEST
            )

            receivers = NotificationService.send_notification_to_users(
                db=db, user_ids=[game.organizer_id], notification=notification
            )

            return JoinResult(
                join_request=join_request,
                notification=notification,
                receivers=receivers,
            )
        else:
            participant = ParticipantService.create_participant(db, user_id, game.id)

            notification = NotificationService.create_notification(
                db=db, game_id=game.id, text=NotificationsData.NEW_PARTICIPANT_IN_GAME
            )

            receivers = NotificationService.send_notification_to_users(
                db=db, user_ids=[game.organizer_id], notification=notification
            )

            return JoinResult(
                participant=participant, notification=notification, receivers=receivers
            )

    @staticmethod
    def update_game_data(
        db: Session, game_id: int, new_game_data: GameUpdateData, organizer_id: int
    ) -> Game:
        """Update game data"""
        game = db.query(Game).filter(Game.id == game_id).first_not_deleted()
        if not game:
            raise ValueError("Игра не найдена!")

        if game.organizer_id != organizer_id:
            raise ValueError("Данные действия доступны только организатору игры")

        if new_game_data.title != game.title:
            if len(new_game_data.title.strip()) < 2:
                raise ValueError("Слишком короткое название игры")
            game.title = new_game_data.title.strip()

        if new_game_data.is_private is not NOT_PROVIDED:
            game.is_private = new_game_data.is_private

        if new_game_data.description != game.description:
            game.description = new_game_data.description

        if new_game_data.budget != game.budget:
            if new_game_data.budget and new_game_data.budget < 0:
                raise ValueError("Бюджет игры не может быть отрицательным")
            game.budget = new_game_data.budget

        if new_game_data.event_date != game.event_date:
            new_game_data.event_date = GameService._validate_event_date(
                new_game_data.event_date
            )
            game.event_date = new_game_data.event_date

        if new_game_data.status != game.status:
            if new_game_data.status.lower().strip() not in GameStatus.ALL:
                raise ValueError("Недопустимый статус игры")
            game.status = new_game_data.status.lower().strip()

        db.commit()
        db.refresh(game)

        return game

    @staticmethod
    def get_filtered_user_games(
        db: Session, user_id: int, role: str = "all", game_status: str = "all"
    ) -> List[Game]:
        """Getting user games by filters"""
        query = db.query(Game).not_deleted()

        if role == "organizer":
            query = query.filter(Game.organizer_id == user_id)
        elif role == "participant":
            query = query.join(Participant).filter(Participant.user_id == user_id)
        elif role == "all":
            query = query.outerjoin(Participant).filter(
                or_(Game.organizer_id == user_id, Participant.user_id == user_id)
            )
        else:
            raise ValueError("Неверное значение для фильтрации")

        if game_status == GameStatus.ACTIVE:
            query = query.filter(Game.status == GameStatus.ACTIVE)
        elif game_status == GameStatus.DRAFT:
            query = query.filter(Game.status == GameStatus.DRAFT)
        elif game_status == GameStatus.COMPLETED:
            query = query.filter(Game.status == GameStatus.COMPLETED)
        elif game_status == "all":
            pass
        else:
            raise ValueError("Неверное значение для фильтрации")

        return query.distinct().order_by(Game.created_at.desc()).all()

    @staticmethod
    def delete_game(db: Session, organizer_id: int, game_id: int) -> Optional[str]:
        """Delete game by soft delete"""
        organizer = db.get(User, organizer_id)
        if not organizer:
            raise ValueError("Пользователь не найден")

        game = db.query(Game).filter(Game.id == game_id).first_not_deleted()
        if not game:
            raise ValueError("Игра не найдена")

        if game.organizer_id != organizer.id:
            raise ValueError("Данные действия доступны только организатору игры")

        game.soft_delete()
        db.commit()
        return "Игра успешно удалена"

    @staticmethod
    def get_game_by_id(db: Session, game_id: int, user_id: int) -> Game:
        """Getting game by id"""
        game = db.query(Game).filter(Game.id == game_id).first_not_deleted()
        if not game:
            raise ValueError("Игра не найдена")
        participant = (
            db.query(Participant)
            .filter(Participant.game_id == game.id, Participant.user_id == user_id)
            .first_not_deleted()
        )

        if game.organizer_id != user_id and participant is None:
            raise ValueError("Игра не найдена для пользователя")

        return game
