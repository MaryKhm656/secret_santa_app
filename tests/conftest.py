import pytest

from app.schemas.games import GameCreateData
from app.schemas.users import UserCreateData
from app.service.draw_service import DrawService
from app.service.game_service import GameService
from app.service.user_service import UserService
from tests.constants.data import (
    Organizer,
    TestGameData,
    TestUser1,
    TestUser2,
    TestUser3,
)
from tests.constants.db import SessionLocal, drop_test_db, init_test_db


@pytest.fixture()
def init_db():
    init_test_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
    drop_test_db()


@pytest.fixture
def first_user_data():
    return UserCreateData(
        email=TestUser1.email, password=TestUser1.password, username=TestUser1.username
    )


@pytest.fixture
def second_user_data():
    return UserCreateData(
        email=TestUser2.email, password=TestUser2.password, username=TestUser2.username
    )


@pytest.fixture
def third_user_data():
    return UserCreateData(
        email=TestUser3.email, password=TestUser3.password, username=TestUser3.username
    )


@pytest.fixture
def organizer_user_data():
    return UserCreateData(
        email=Organizer.email, password=Organizer.password, username=Organizer.username
    )


@pytest.fixture
def create_four_test_users(
    init_db, first_user_data, second_user_data, third_user_data, organizer_user_data
):
    db = init_db
    first_user = UserService.create_user(db, first_user_data)
    second_user = UserService.create_user(db, second_user_data)
    third_user = UserService.create_user(db, third_user_data)
    organizer_user = UserService.create_user(db, organizer_user_data)
    return db, first_user, second_user, third_user, organizer_user


@pytest.fixture
def create_default_test_game(create_four_test_users):
    db, first_user, second_user, third_user, organizer = create_four_test_users
    game_create_data = GameCreateData.from_db(
        db=db, title=TestGameData.title, organizer_id=organizer.id
    )
    game = GameService.create_game(db, game_create_data)
    return db, game, first_user, second_user, third_user, organizer


@pytest.fixture
def create_default_test_private_game(create_four_test_users):
    db, first_user, second_user, third_user, organizer = create_four_test_users
    game_create_data = GameCreateData.from_db(
        db=db, title=TestGameData.title, organizer_id=organizer.id, is_private=True
    )
    game = GameService.create_game(db, game_create_data)
    return db, game, first_user, second_user, third_user, organizer


@pytest.fixture
def create_game_with_participants_for_draw(create_default_test_game):
    db, game, first_user, second_user, third_user, organizer = create_default_test_game
    GameService.join_the_game(db, first_user.id, game.secret_key)
    GameService.join_the_game(db, second_user.id, game.secret_key)
    GameService.join_the_game(db, third_user.id, game.secret_key)
    return db, game, first_user, second_user, third_user, organizer
