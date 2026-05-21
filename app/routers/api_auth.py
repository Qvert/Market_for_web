from fastapi import APIRouter, Request, status, HTTPException, Depends, Query
from pydantic import BaseModel, EmailStr

from app.data import USERS
from app.security import get_hash_password, verify_password, get_current_user

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class UserRegister(BaseModel):
    name: str
    password: str
    email: EmailStr


class UserLogin(BaseModel):
    email: EmailStr
    password: str


@router.get("/check-email")
async def check_email(email: str = Query(...)):
    """
    Проверяет, существует ли пользователь с таким email.
    Вызывается из JS при событии 'blur' на поле email.
    """
    is_exists = email in USERS
    return {"exists": is_exists}


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):
    if user.email in USERS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email уже занят"
        )

    hashed_password = get_hash_password(user.password)

    USERS[user.email] = {
        "name": user.name,
        "email": user.email,
        "password": hashed_password
    }
    return {"message": "Пользователь успешно зарегистрирован"}


@router.post("/login")
async def login_user(user: UserLogin, request: Request):
    db_user = USERS.get(user.email)

    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный email или пароль"
        )

    request.session["user"] = db_user["email"]
    return {"message": "Успешный вход"}


@router.post("/logout")
async def logout(request: Request):
    request.session.pop("user", None)
    return {"message": "Успешный выход"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    return {"name": current_user["name"], "email": current_user["email"]}