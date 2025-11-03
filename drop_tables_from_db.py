from app.db.database import drop_all
from app.db.models import (
    User,
    Game,
    JoinRequest,
    Participant,
    Restriction,
    Draw,
    DrawAssignment,
    Gift,
    Message,
    Notification
)


if __name__ == "__main__":
    drop_all()