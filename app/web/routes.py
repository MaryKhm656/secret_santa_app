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
from app.schemas.games import GameCreateData
from app.schemas.users import UserCreateData
from app.service.game_service import GameService
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
                "new_game_key": request.cookies.get(
                    "new_game_key"
                ),  # Для показа ключа после создания
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
        event_date_dt = datetime.fromisoformat(event_date.replace("Z", "+00:00"))

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
            event_date=event_date_dt,
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
