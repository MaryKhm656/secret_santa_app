from dataclasses import dataclass
from typing import List, Optional

from app.db.models import JoinRequest, Participant, NotificationReceiver

NULL_DATA = object()


@dataclass
class JoinResult:
    participant: Optional[Participant] = NULL_DATA
    join_request: Optional[JoinRequest] = NULL_DATA
    notification_receiver: List[NotificationReceiver] = NULL_DATA
