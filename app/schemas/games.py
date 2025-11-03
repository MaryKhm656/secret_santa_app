from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.core.security import generate_secret_key_for_game


@dataclass
class GameCreateData:
    title: str
    organizer_id: int
    is_private: bool = False
    secret_key: str = generate_secret_key_for_game()
    description: Optional[str] = None
    budget: Optional[float] = None
    event_date: Optional[datetime] = None
