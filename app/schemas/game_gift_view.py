from dataclasses import dataclass
from typing import Optional

from app.db.models import Game, Gift, Participant


@dataclass
class GameGiftView:
    game: Game
    participation: Participant
    my_gift: Optional[Gift]
    gift_for_me: Optional[Gift]
