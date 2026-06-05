from fastapi import HTTPException, status
from .repository import auth_repository
from .models import User, UserRegister, UserLogin
from app.security import get_hash_password, verify_password

class AuthService:
    def register(self, data: UserRegister) -> User:
        if auth_repository.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email уже занят")
        
        user = User(
            id=auth_repository.count() + 1,
            name=data.name,
            email=data.email,
            password=get_hash_password(data.password)
        )
        auth_repository.save(user)
        return user

    def authenticate(self, data: UserLogin) -> User:
        user = auth_repository.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password):
            raise HTTPException(status_code=401, detail="Неверный email или пароль")
        return user

    def check_email_exists(self, email: str) -> bool:
        return auth_repository.get_by_email(email) is not None

auth_service = AuthService()
