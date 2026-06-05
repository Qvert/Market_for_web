from typing import Dict, Optional
from .models import User

class AuthRepository:
    def __init__(self):
        self._users: Dict[str, User] = {}

    def get_by_email(self, email: str) -> Optional[User]:
        return self._users.get(email)

    def save(self, user: User):
        self._users[user.email] = user

    def count(self) -> int:
        return len(self._users)

auth_repository = AuthRepository()
