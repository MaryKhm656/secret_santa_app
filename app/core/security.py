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
