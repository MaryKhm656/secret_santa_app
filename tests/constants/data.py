import datetime
from dataclasses import dataclass
from datetime import timedelta

from app.constants import GameStatus


@dataclass
class TestUser1:
    username: str = "Test User"
    email: str = "test@mail.com"
    password: str = "TestPassword1234"


@dataclass
class TestUser2:
    username: str = "Test User 2"
    email: str = "test2@mail.com"
    password: str = "TestPassword12345"


@dataclass
class TestUser3:
    username: str = "Test User 3"
    email: str = "test3@mail.com"
    password: str = "TestPassword123456"


@dataclass
class Organizer:
    username: str = "Organizer"
    email: str = "organizer@mail.com"
    password: str = "TestPassword1234567"


class TestGameData:
    title = "Test Game"
    description = "Test description for test game"
    budget = 1000.0
    event_date = datetime.datetime.now() + timedelta(days=5)
    status = GameStatus.ACTIVE
