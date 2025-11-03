from dataclasses import dataclass
from typing import List, Optional

from app.db.models import JoinRequest, Notification, Participant

NULL_DATA = object()


@dataclass
class JoinResult:
    participant: Optional[Participant] = NULL_DATA
    join_request: Optional[JoinRequest] = NULL_DATA
    notifications: List[Notification] = NULL_DATA
