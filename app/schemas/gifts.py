from dataclasses import dataclass
from typing import Optional

NOT_PROVIDED = object()


@dataclass
class GiftCreateData:
    participant_id: int
    receiver_participant_id: int
    game_id: int
    title: str
    description: str
    price: float


@dataclass
class GiftUpdateData:
    title: Optional[str] = NOT_PROVIDED
    description: Optional[str] = NOT_PROVIDED
    price: Optional[float] = NOT_PROVIDED
