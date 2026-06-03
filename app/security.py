import bcrypt
from fastapi import Request, HTTPException, status

from app.data import USERS

def get_hash_password(password: str) -> str:
    """
    Хеширование пароля. 
    1. Переводим строку в байты.
    2. Генерируем соль и хешируем.
    3. Возвращаем как строку для хранения в БД.
    """
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(pwd_bytes, salt)
    return hashed_password.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Проверка пароля.
    Сравнивает чистый пароль с хешем.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_current_user(request: Request):
    """
    Зависимость для проверки авторизации пользователя.
    """
    user_email = request.session.get("user")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется аутентификация"
        )

    return USERS.get(user_email)