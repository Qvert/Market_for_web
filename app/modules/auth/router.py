from fastapi import APIRouter, Request, status, Depends, Query
from .service import auth_service
from .models import UserRegister, UserLogin
from app.security import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.get("/check-email")
async def check_email(email: str = Query(...)):
    return {"exists": auth_service.check_email_exists(email)}

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    auth_service.register(user_data)
    return {"message": "Пользователь успешно зарегистрирован"}

@router.post("/login")
async def login(user_data: UserLogin, request: Request):
    user = auth_service.authenticate(user_data)
    request.session["user"] = user.email
    return {"message": "Успешный вход"}

@router.post("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return {"message": "Успешный выход"}

@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    return {"name": current_user.name, "email": current_user.email}
