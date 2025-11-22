from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.environs import SECRET_KEY
from app.core.security import verify_password
from app.db.database import SessionLocal
from app.db.models import User

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Creates a JWT access token with the specified data and lifetime"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """
    Gets the current user from the JWT token

    :param token:
    :return User:
    """
    credential_exception = HTTPException(
        status_code=401,
        detail="Не удалось проверить токен",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise credential_exception
    except JWTError:
        raise credential_exception

    session = SessionLocal()
    user = session.query(User).filter_by(id=user_id).first()
    session.close()
    if not user:
        raise credential_exception
    return user


def login_user(email: str, password: str) -> str:
    """
    Authenticates the user and returns a JWT token

    :param email:
    :param password:
    :return JWT access token:
    """
    session = SessionLocal()
    user = session.query(User).filter(User.email == email).first_not_deleted()
    session.close()

    if not user or not verify_password(password, user.password_hash):
        raise ValueError("Неверный email или пароль")

    return create_access_token(data={"sub": str(user.id)})


def get_current_user_from_cookie(request: Request) -> User:
    """
    Gets the current user from the JWT token in the cookie.

    :param request:
    :return User:
    """
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Токен не найден в cookie")

    credential_exception = HTTPException(
        status_code=401,
        detail="Не удалось проверить токен",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise credential_exception
    except JWTError:
        raise credential_exception

    session = SessionLocal()
    user = session.query(User).filter(User.id == user_id).first_not_deleted()
    session.close()

    if not user:
        raise credential_exception

    return user
