from dataclasses import dataclass
from typing import Optional

NOT_PROVIDED = object()


@dataclass
class UserCreateData:
    email: str
    password: str
    username: Optional[str] = None


@dataclass
class UserUpdateData:
    username: Optional[str] = NOT_PROVIDED
    email: Optional[str] = NOT_PROVIDED
