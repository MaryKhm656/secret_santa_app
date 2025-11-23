from app.service.user_service import UserService


def test_create_account(init_db, first_user_data):
    """
    Scenario

    1. Create user with default test data
    2. Check user was saved
    """
    db = init_db
    user_create_data = first_user_data
    user = UserService.create_user(db, user_create_data)

    assert (
        user.username == user_create_data.username
    ), f"{user.username} not equal to {user_create_data.username}"
    assert (
        user.email == user_create_data.email
    ), f"{user.email} not equal to {user_create_data.email}"
