from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from sqlalchemy.orm import Session

from app.constants import GameStatus
from app.core.security import generate_secret_key_for_game

NOT_PROVIDED = object()


@dataclass
class GameCreateData:
    title: str
    organizer_id: int
    is_private: bool = False
    secret_key: Optional[str] = None
    description: Optional[str] = None
    budget: Optional[float] = None
    event_date: Union[datetime, str] = None
    status: str = GameStatus.DRAFT

    @classmethod
    def from_db(cls, db: Session, **kwargs):
        secret_key = generate_secret_key_for_game(db)
        return cls(secret_key=secret_key, **kwargs)


@dataclass
class GameUpdateData:
    title: Optional[str] = NOT_PROVIDED
    is_private: Optional[bool] = NOT_PROVIDED
    description: Optional[str] = NOT_PROVIDED
    budget: Optional[float] = NOT_PROVIDED
    event_date: Union[datetime, str] = NOT_PROVIDED
    status: Optional[str] = NOT_PROVIDED
