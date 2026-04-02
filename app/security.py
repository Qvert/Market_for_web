from passlib.context import CryptContext
from fastapi import Request, HTTPException, status

from app.data import USERS

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_hash_password(password):
    return pwd_context.hash(password)

def get_current_user(request: Request):
    """
    Зависимость (Dependency) для проверки авторизации пользователя.
    Если юзера нет в сессии, выбрасывает ошибку 401.
    """
    user_email = request.session.get("user")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )
    return USERS.get(user_email)