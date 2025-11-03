from app.db.database import init_db
from app.db.models import (
    Draw,
    DrawAssignment,
    Game,
    Gift,
    Message,
    Notification,
    Participant,
    Restriction,
    User,
)

if __name__ == "__main__":
    init_db()
