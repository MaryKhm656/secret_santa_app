import secrets
from string import ascii_lowercase, ascii_uppercase, digits

from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


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


def generate_secret_key_for_game() -> str:
    characters = ascii_lowercase + ascii_uppercase + digits
    return "".join(secrets.choice(characters) for _ in range(10))
