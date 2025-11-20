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
from app.schemas.users import UserCreateData
from app.service.draw_service import DrawService
from app.service.game_service import GameService
from app.service.join_requset_service import JoinRequestService
from app.service.user_service import UserService

templates = Jinja2Templates(directory="templates")

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def reed_root(request: Request, current_user=Depends(get_template_user)):
    return templates.TemplateResponse(
        "home.html", {"request": request, "current_user": current_user}
    )


@router.get("/register", response_class=HTMLResponse)
async def register_form(
    request: Request,
    message: str = None,
    current_user: User = Depends(get_template_user),
):
    """
    New user registration page.

    returns:
    TemplateResponse: Registration page or redirect if the user is already authenticated
    """
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
    """
    Processing the new user registration form.

    returns:
    RedirectResponse: Redirect to the login page on success
    TemplateResponse: Registration page with an error on failure
    """
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
    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "current_user": current_user},
    )


@router.get("/login", response_class=HTMLResponse)
async def login_form(request: Request, current_user: User = Depends(get_template_user)):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "current_user": current_user},
    )


@router.post("/login", response_class=HTMLResponse)
async def login_form_submit(
    request: Request, email: str = Form(...), password: str = Form(...)
):
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
    """
    Logging the user out.

    returns:
    RedirectResponse: Redirect to the main page with the access token removed
    """
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
    update_user = UserService.update_wishlist(db, current_user.id, wishlist_text)

    return templates.TemplateResponse(
        "profile.html", {"request": request, "current_user": update_user}
    )


@router.get("/create-game", response_class=HTMLResponse)
async def get_create_game(
    request: Request,
    current_user: User = Depends(get_template_user),
):
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
    """Обработка присоединения к игре"""
    try:
        result = GameService.join_the_game(db, current_user.id, secret_key)

        if hasattr(result, "participant"):
            message = "🎉 Вы успешно присоединились к игре!"
        else:
            message = "📨 Заявка на вступление отправлена организатору!"

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
                "sent_requests": sent_requests,
                "pending_requests": pending_requests,
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
    try:
        DrawService.start_draw(db, current_user.id, game_id)

        return RedirectResponse(url=f"/game/{game_id}", status_code=302)

    except ValueError as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "current_user": current_user, "error": str(e)},
            status_code=400,
        )
