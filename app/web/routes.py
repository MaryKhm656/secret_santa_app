from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Form, Request
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from app.core.auth import login_user
from app.db.models import User
from app.dependencies import get_db, get_template_user
from app.schemas.games import GameCreateData, GameUpdateData
from app.schemas.gifts import GiftCreateData, GiftUpdateData
from app.schemas.join_requests import NULL_DATA
from app.schemas.users import UserCreateData, UserUpdateData
from app.service.draw_service import DrawService
from app.service.game_service import GameService
from app.service.gift_service import GiftService
from app.service.join_requset_service import JoinRequestService
from app.service.participant_service import ParticipantService
from app.service.user_service import UserService

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def reed_root(request: Request, current_user=Depends(get_template_user)):
    """Home page"""
    return templates.TemplateResponse(
        "home.html", {"request": request, "current_user": current_user}
    )


@router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    message: str = None,
    current_user: User = Depends(get_template_user),
):
    """New user registration page"""
    if current_user:
        return RedirectResponse(url="/")
    return templates.TemplateResponse(
        "register.html",
        {"request": request, "current_user": current_user, "message": message},
    )


@router.post("/register", response_class=HTMLResponse)
async def register_form_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Processing the new user registration form."""
    try:
        user_data = UserCreateData(email=email, password=password, username=username)
        user = UserService.create_user(db, user_data)

        access_token = login_user(user.email, password)
        response = RedirectResponse(url="/profile", status_code=302)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response

    except ValidationError as e:
        error_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": " | ".join(error_msgs)},
            status_code=400,
        )

    except ValueError as e:
        return templates.TemplateResponse(
            "register.html", {"request": request, "error": str(e)}
        )

    except SQLAlchemyError:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Ошибка при работе с базой данных"},
            status_code=500,
        )


@router.get("/profile", response_class=HTMLResponse)
async def user_profile(
    request: Request,
    current_user: User = Depends(get_template_user),
):
    """User profile page"""
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, current_user: User = Depends(get_template_user)):
    """Login page"""
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "current_user": current_user},
    )


@router.post("/login", response_class=HTMLResponse)
async def login_form_submit(
    request: Request, email: str = Form(...), password: str = Form(...)
):
    """Process user login"""
    try:
        access_token = login_user(email, password)

        response = RedirectResponse(url="/profile", status_code=302)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response
    except ValueError as e:
        return templates.TemplateResponse(
            "login.html", {"request": request, "error": str(e)}, status_code=400
        )
    except SQLAlchemyError:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Ошибка при работе с базой данных"},
            status_code=500,
        )


@router.get("/logout")
async def logout_user():
    """Logging the user out"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("access_token")
    return response


@router.post("/update-wishlist", response_class=HTMLResponse)
async def update_wishlist(
    request: Request,
    wishlist_text: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_template_user),
):
    """Updated user wishlist form"""
    update_user = UserService.update_wishlist(db, current_user.id, wishlist_text)

    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": update_user}
    )


@router.get("/create-game", response_class=HTMLResponse)
async def get_create_game(
    request: Request,
    current_user: User = Depends(get_template_user),
):
    """Create game form page"""
    return templates.TemplateResponse(
        "create-game.html", {"request": request, "current_user": current_user}
    )


@router.get("/games", response_class=HTMLResponse)
async def user_games(
    request: Request,
    role: str = "all",
    status: str = "all",
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """User's games list with filtering"""
    try:
        games = GameService.get_filtered_user_games(
            db, user_id=current_user.id, role=role, game_status=status
        )

        return templates.TemplateResponse(
            "games.html",
            {
                "request": request,
                "current_user": current_user,
                "games": games,
                "current_role": role,
                "current_status": status,
                "new_game_key": request.cookies.get("new_game_key"),
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            "games.html",
            {
                "request": request,
                "current_user": current_user,
                "games": [],
                "error": str(e),
                "current_role": role,
                "current_status": status,
            },
        )


@router.post("/create-game", response_class=HTMLResponse)
async def create_game_submit(
    request: Request,
    title: str = Form(...),
    description: str = Form(None),
    budget: Optional[str] = Form(None),
    event_date: str = Form(...),
    is_private: bool = Form(False),
    status: str = Form("registration"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_template_user),
):
    """Process game creation"""
    try:
        if event_date:
            event_date = datetime.fromisoformat(event_date.replace("Z", "+00:00"))

        if budget == "":
            budget = None
        else:
            budget = float(budget)

        game_data = GameCreateData.from_db(
            db=db,
            title=title,
            organizer_id=current_user.id,
            is_private=is_private,
            description=description,
            budget=budget,
            event_date=event_date,
            status=status,
        )

        game = GameService.create_game(db, game_data)

        response = RedirectResponse(url="/games", status_code=302)
        response.set_cookie(
            key="new_game_key", value=game.secret_key, max_age=30, httponly=False
        )
        return response

    except ValueError as e:
        return templates.TemplateResponse(
            "create-game.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )

    except Exception as e:
        return templates.TemplateResponse(
            "create-game.html",
            {
                "request": request,
                "current_user": current_user,
                "error": f"Ошибка при создании игры: {str(e)}",
            },
            status_code=500,
        )


@router.post("/delete-game/{game_id}")
async def delete_game(
    request: Request,
    game_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Delete game"""
    try:
        GameService.delete_game(db, current_user.id, game_id)
        return RedirectResponse(url="/games", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse(
            "games.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.get("/game/{game_id}", response_class=HTMLResponse)
async def get_game(
    request: Request,
    game_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """View game page"""
    try:
        game = GameService.get_game_by_id(db, game_id, current_user.id)

        return templates.TemplateResponse(
            "game-view.html",
            {"request": request, "current_user": current_user, "game": game},
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": e},
            status_code=500,
        )


@router.get("/edit-game/{game_id}", response_class=HTMLResponse)
async def get_edit_game(
    request: Request,
    game_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Edit game form"""
    game = GameService.get_game_by_id(db, game_id, current_user.id)

    return templates.TemplateResponse(
        "edit-game.html",
        {"request": request, "game": game, "current_user": current_user},
    )


@router.post("/edit-game/{game_id}", response_class=HTMLResponse)
async def post_edit_game(
    request: Request,
    game_id: int,
    title: str = Form(...),
    description: str = Form(None),
    budget: Optional[str] = Form(None),
    event_date: str = Form(...),
    is_private: bool = Form(False),
    status: str = Form("registration"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_template_user),
):
    """Process for edit game"""
    try:
        if event_date:
            event_date = datetime.fromisoformat(event_date.replace("Z", "+00:00"))

        if budget == "":
            budget = None
        else:
            budget = float(budget)

        new_game_data = GameUpdateData(
            title=title,
            is_private=is_private,
            description=description,
            budget=budget,
            event_date=event_date,
            status=status,
        )

        GameService.update_game_data(db, game_id, new_game_data, current_user.id)

        response = RedirectResponse(url="/games", status_code=302)
        return response

    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": e},
            status_code=500,
        )


@router.post("/join-game", response_class=HTMLResponse)
async def join_game_submit(
    request: Request,
    secret_key: str = Form(...),
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Processing game joins"""
    try:
        result = GameService.join_the_game(db, current_user.id, secret_key)

        if result.join_request and result.join_request is not NULL_DATA:
            message = "📨 Заявка на вступление отправлена организатору!"
        else:
            message = "🎉 Вы успешно присоединились к игре!"

        return HTMLResponse(content=message, status_code=200)

    except ValueError as e:
        return HTMLResponse(content=str(e), status_code=400)
    except Exception as e:
        return HTMLResponse(content=str(e), status_code=500)


@router.get("/requests", response_class=HTMLResponse)
async def view_requests(
    request: Request,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """View request page"""
    try:
        sent_requests = JoinRequestService.get_user_join_requests(db, current_user.id)

        pending_requests = JoinRequestService.get_pending_requests_for_organizer(
            db, current_user.id
        )

        return templates.TemplateResponse(
            "requests.html",
            {
                "request": request,
                "current_user": current_user,
                "sent_requests": sent_requests if sent_requests is not None else [],
                "pending_requests": pending_requests
                if pending_requests is not None
                else [],
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "current_user": current_user,
                "error": f"Ошибка при загрузке заявок: {str(e)}",
            },
            status_code=500,
        )


@router.post("/requests/{request_id}/approve", response_class=HTMLResponse)
async def approve_request(
    request: Request,
    request_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Approve join request"""
    try:
        JoinRequestService.approve_join_request(db, request_id, current_user.id)
        return RedirectResponse(url="/requests", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.post("/requests/{request_id}/reject", response_class=HTMLResponse)
async def reject_request(
    request: Request,
    request_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Reject join request"""
    try:
        JoinRequestService.reject_join_request(db, request_id, current_user.id)
        return RedirectResponse(url="/requests", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.post("/game/{game_id}/start-draw", response_class=HTMLResponse)
async def start_draw(
    request: Request,
    game_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Start gift draw for game"""
    try:
        DrawService.start_draw(db, current_user.id, game_id)

        return RedirectResponse(url=f"/game/{game_id}", status_code=302)

    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.get("/gifts", response_class=HTMLResponse)
async def view_gifts(
    request: Request,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """View gifts page"""
    try:
        games_data = GiftService.get_user_gifts_overview(db, current_user.id)

        return templates.TemplateResponse(
            "gifts.html",
            {
                "request": request,
                "current_user": current_user,
                "games_data": games_data,
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "current_user": current_user,
                "error": f"Ошибка при загрузке подарков: {str(e)}",
            },
            status_code=500,
        )


@router.get("/game/{game_id}/create-gift", response_class=HTMLResponse)
async def create_gift_form(
    request: Request,
    game_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """create gift page"""
    try:
        game = GameService.get_game_by_id(db, game_id, current_user.id)
        participant = next(
            (
                participant
                for participant in game.participants
                if participant.user_id == current_user.id
            ),
            None,
        )
        receiver = participant.assigned_to

        return templates.TemplateResponse(
            "create-gift.html",
            {
                "request": request,
                "current_user": current_user,
                "game": game,
                "receiver": receiver,
                "participant": participant,
            },
        )

    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.post("/game/{game_id}/create-gift", response_class=HTMLResponse)
async def create_gift_submit(
    request: Request,
    game_id: int,
    title: str = Form(...),
    description: str = Form(None),
    price: Optional[str] = Form(None),
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Process create gift"""
    try:
        game = GameService.get_game_by_id(db, game_id, current_user.id)
        participant = next(
            (
                participant
                for participant in game.participants
                if participant.user_id == current_user.id
            ),
            None,
        )

        if price == "":
            price = None
        else:
            price = float(price)

        gift_create_data = GiftCreateData(
            participant_id=participant.id,
            receiver_participant_id=participant.assigned_to_id,
            game_id=game_id,
            title=title,
            description=description,
            price=price,
        )

        GiftService.create_gift(db, gift_create_data)

        return RedirectResponse(url="/gifts", status_code=302)

    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.post("/gifts/{gift_id}/update-status", response_class=HTMLResponse)
async def update_gift_status(
    request: Request,
    gift_id: int,
    new_status: str = Form(...),
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Process updating gift status"""
    try:
        participant = ParticipantService.get_participant_by_user_id(db, current_user.id)
        GiftService.update_gift_status(db, gift_id, participant.id, new_status)
        return RedirectResponse(url="/gifts", status_code=302)

    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.get("/gifts/{gift_id}/edit", response_class=HTMLResponse)
async def get_edit_gift(
    request: Request,
    gift_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Edit gift page"""
    gift = GiftService.get_gift_by_id(db, gift_id)
    game = GameService.get_game_by_id(db, gift.game_id, current_user.id)
    participant = next(
        (
            participant
            for participant in game.participants
            if participant.user_id == current_user.id
        ),
        None,
    )
    receiver = participant.assigned_to

    return templates.TemplateResponse(
        "edit-gift.html",
        {
            "request": request,
            "current_user": current_user,
            "gift": gift,
            "receiver": receiver,
            "participant": participant,
            "game": game,
        },
    )


@router.post("/gifts/{gift_id}/edit", response_class=HTMLResponse)
async def update_gift_submit(
    request: Request,
    gift_id: int,
    title: str = Form(...),
    description: str = Form(None),
    price: Optional[str] = Form(None),
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Process updating gift data"""
    try:
        if price == "":
            price = None
        else:
            price = float(price)

        gift_update_data = GiftUpdateData(title, description, price)

        GiftService.update_gift_data(db, gift_update_data, gift_id)

        return RedirectResponse(url="/gifts", status_code=302)

    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.post("/gifts/{gift_id}/delete")
async def delete_gift(
    request: Request,
    gift_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Delete gift"""
    try:
        GiftService.delete_gift(db, gift_id)
        return RedirectResponse(url="/gifts", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse(
            "gifts.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )


@router.get("/edit-profile/{user_id}", response_class=HTMLResponse)
async def get_edit_user(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_template_user),
):
    """Edit user data page"""
    return templates.TemplateResponse(
        "edit-profile.html", {"request": request, "current_user": current_user}
    )


@router.post("/edit-profile/{user_id}", response_class=HTMLResponse)
async def edit_user_data_submit(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_template_user),
    username: str = Form(...),
    email: str = Form(...),
):
    """Process updating user data"""
    try:
        new_user_data = UserUpdateData(username, email)
        UserService.update_user_data(db, current_user.id, new_user_data)
        return RedirectResponse(url="/profile", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse(
            "edit-profile.html",
            {"request": request, "current_user": current_user, "error": str(e)},
        )


@router.post("/delete-user/{user_id}")
async def delete_user(
    request: Request,
    user_id: int,
    current_user: User = Depends(get_template_user),
    db: Session = Depends(get_db),
):
    """Process delete user"""
    try:
        UserService.delete_user(db, user_id)
        response = RedirectResponse(url="/", status_code=302)
        response.delete_cookie("access_token")
        return response
    except ValueError as e:
        return templates.TemplateResponse(
            "gifts.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )
