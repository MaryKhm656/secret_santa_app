from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union

from app.constants import GameStatus
from app.core.security import generate_secret_key_for_game

NOT_PROVIDED = object()


@dataclass
class GameCreateData:
    title: str
    organizer_id: int
    is_private: bool = False
    secret_key: str = generate_secret_key_for_game()
    description: Optional[str] = None
    budget: Optional[float] = None
    event_date: Union[datetime, str] = None
    status: str = GameStatus.DRAFT

@dataclass
class GameUpdateData:
    title: Optional[str] = NOT_PROVIDED
    is_private: Optional[bool] = NOT_PROVIDED
    secret_key: Optional[str] = NOT_PROVIDED
    description: Optional[str] = NOT_PROVIDED
    budget: Optional[float] = NOT_PROVIDED
    event_date: Union[datetime, str] = NOT_PROVIDED
    status: Optional[str] = NOT_PROVIDED
