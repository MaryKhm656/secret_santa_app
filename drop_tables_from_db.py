from app.db.database import drop_all
from app.db.models import (  # noqa: F401
    Draw,
    DrawAssignment,
    Game,
    Gift,
    JoinRequest,
    Notification,
    Participant,
    User,
)

if __name__ == "__main__":
    drop_all()
