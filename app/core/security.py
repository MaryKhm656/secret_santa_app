import secrets
from string import ascii_lowercase, ascii_uppercase, digits

from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.db.models import Game

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"], deprecated="auto", pbkdf2_sha256__default_rounds=300000
)


def hash_password(password: str) -> str:
    """
    Hashes a password using bcrypt

    :param password:
    :return hashed password:
    """
    return pwd_context.hash(password)


def verify_password(expected_password: str, hashed_password: str) -> bool:
    """Checks whether a password matches its hash"""
    return pwd_context.verify(expected_password, hashed_password)


def generate_secret_key_for_game(db: Session) -> str:
    while True:
        characters = ascii_lowercase + ascii_uppercase + digits
        key = "".join(secrets.choice(characters) for _ in range(10))
        existing_key = db.query(Game).filter_by(secret_key=key).first()
        if not existing_key:
            return key
