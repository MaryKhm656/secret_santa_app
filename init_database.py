from app.db.database import init_db
from app.db.models import (
    User,
    Game,
    JoinRequest,
    Participant,
    Draw,
    DrawAssignment,
    Gift,
    Message,
    Notification
)

if __name__ == "__main__":
    init_db()
