from app.constants import JoinRequestStatus, NotificationsData
from app.schemas.games import GameCreateData
from app.schemas.join_requests import NULL_DATA
from app.service.game_service import GameService
from tests.constants.data import TestGameData


def test_create_game_with_required_field(create_four_test_users):
    """
    Scenario

    1. Create test game with required fields
    2. Check game was saved
    """
    db, _, _, _, organizer = create_four_test_users
    game_create_data = GameCreateData.from_db(
        db=db, title=TestGameData.title, organizer_id=organizer.id
    )
    game = GameService.create_game(db, game_create_data)

    assert (
        game.title == game_create_data.title
    ), f"{game.title} not equal to {game_create_data.title}"
    assert (
        game.organizer_id == organizer.id
    ), f"{game.organizer_id} not equal to {organizer.id}"


def test_create_game_with_all_filling_fields(create_four_test_users):
    """
    Scenario

    1. Create test game with all filling fields
    2. Check game was saved
    """
    db, _, _, _, organizer = create_four_test_users
    game_create_data = GameCreateData.from_db(
        db=db,
        title=TestGameData.title,
        organizer_id=organizer.id,
        description=TestGameData.description,
        budget=TestGameData.budget,
        event_date=TestGameData.event_date,
        status=TestGameData.status,
    )
    game = GameService.create_game(db, game_create_data)

    assert (
        game.description == game_create_data.description
    ), f"{game.description} not equal to {game_create_data.description}"
    assert (
        game.budget == game_create_data.budget
    ), f"{game.budget} not equal to {game_create_data.budget}"
    assert (
        game.event_date == game_create_data.event_date
    ), f"{game.event_date} not equal to {game_create_data.event_date}"
    assert (
        game.status == game_create_data.status
    ), f"{game.status} not equal to {game_create_data.status}"


def test_join_the_public_game(create_default_test_game):
    """
    Scenario

    1. Create default test game with required fields and user
    2. Join the game by secret key
    3. Check operation success
    """
    db, game, first_user, _, _, organizer = create_default_test_game
    join_result = GameService.join_the_game(
        db=db, secret_key=game.secret_key, user_id=first_user.id
    )

    assert (
        join_result.participant.user_id == first_user.id
    ), f"{join_result.participant.user_id} not equal to {first_user.id}"
    assert join_result.notification.text == NotificationsData.NEW_PARTICIPANT_IN_GAME, (
        f"{join_result.notification.text} not equal to "
        f"{NotificationsData.NEW_PARTICIPANT_IN_GAME}"
    )


def test_join_the_private_game(create_default_test_private_game):
    """
    Scenario

    1. Create default test game with required fields and user
    2. Join the game by secret key
    3. Check create join request
    4. Check participant wasn't created
    """
    db, game, first_user, _, _, organizer = create_default_test_private_game
    join_result = GameService.join_the_game(
        db=db, secret_key=game.secret_key, user_id=first_user.id
    )

    assert (
        join_result.participant == NULL_DATA
    ), f"{join_result.participant} is not None"
    assert (
        join_result.join_request.status == JoinRequestStatus.PENDING
    ), f"{join_result.join_request.status} not equal to {JoinRequestStatus.PENDING}"
