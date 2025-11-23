from app.service.draw_service import DrawService


def test_start_draw(create_game_with_participants_for_draw):
    """
    Scenario

    1. Create default test game with three participants
    2. Start draw
    3. Check operation success
    """
    (
        db,
        game,
        first_user,
        second_user,
        third_user,
        organizer,
    ) = create_game_with_participants_for_draw
    draw = DrawService.start_draw(db, organizer.id, game.id)

    assert draw.assignments is not None, f"{draw.assignments} is None"
    assert (
        draw.assignments[0] != draw.assignments[1]
    ), f"{draw.assignments[0]} equal to {draw.assignments[1]}"
    assert game.draws[0].id == draw.id, f"{game.draws[0].id} not equal to {draw.id}"
