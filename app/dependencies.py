from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_from_cookie
from app.db.database import SessionLocal


def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_template_user(request: Request):
    try:
        return get_current_user_from_cookie(request)
    except HTTPException:
        return None
