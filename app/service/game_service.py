from datetime import datetime
from typing import Union, Optional

from sqlalchemy.orm import Session

from app.db.models import Game, User
from app.schemas.games import GameCreateData


class GameService:
    @staticmethod
    def _validate_event_date(event_date: Union[datetime, str]) -> Optional[datetime]:
        """Validates and converts event date of game"""
        if isinstance(event_date, str):
            if not event_date.strip():
                event_date = None
            else:
                try:
                    event_date = datetime.strptime(event_date, "%Y-%m-%d %H-%M")
                except ValueError:
                    raise ValueError("Неверный формат даты. Ожидается формат: 'YYYY-MM-DD HH:MM'")

        if event_date and event_date < datetime.now():
            raise ValueError("Нельзя установить дату проведения игры в прошлом")

        return event_date

    @staticmethod
    def create_game(
            db: Session,
            game_data: GameCreateData
    ) -> Game:
        """Method for creating game model in DB"""
        if len(game_data.title.strip()) < 2:
            raise ValueError("Слишком короткое название игры")

        game_data.event_date = GameService._validate_event_date(game_data.event_date)

        user = db.get(User, game_data.organizer_id)
        if not user:
            raise ValueError("Организатор с таким ID не найден")

        game = Game(
            title=game_data.title,
            description=game_data.description,
            budget=game_data.budget,
            event_date=game_data.event_date,
            secret_key=game_data.secret_key,
            organizer_id=game_data.organizer_id,
            is_private=game_data.is_private
        )
        db.add(game)
        db.commit()
        db.refresh(game)

        return game
