from fastapi import APIRouter, Request, status, Form
from fastapi.responses import HTMLResponse
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_303_SEE_OTHER

from app.config import templates
from app.data import fake_users
from app.security import get_hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/register", response_class=HTMLResponse)
async def get_register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@router.post("/register")
async def register_user(request: Request,
                        email: str = Form(),
                        name: str = Form(),
                        password: str = Form()):
    """
    :param request: Обязательный параметр
    :param email: Email пользователя
    :param name: Имя
    :param password: Пароль для хеширования
    :return: Юзер добавлен
    """
    for user in fake_users:
        if user["email"] == email:
            return templates.TemplateResponse(
                request=request,
                name="register.html",
                context={"error": "Такой email уже существует"}
            )
    hashed_password = get_hash_password(password[:72])

    new_user = {
        "email": email,
        "name": name,
        "password_hash": hashed_password,
    }
    fake_users.append(new_user)

    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/login", response_class=HTMLResponse)
async def get_login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@router.post("/login")
async def login_user(request: Request,
                     email: str = Form(),
                     password: str = Form()
                     ):
    """
    :param request: Обязательный параметр
    :param email: Email пользователя
    :param password: Пароль пользователя
    :return: Добавляем пользователя в сессию
    """
    user_found = None
    for user in fake_users:
        if user["email"] == email:
            user_found = user
            break

    if not user_found or not verify_password(password, user_found["password_hash"]):
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={"error": "Неверный email или пароль"}
        )

    request.session["user"] = {
        "email": user_found["email"],
        "name": user_found["name"]
    }

    return RedirectResponse(url="/", status_code=HTTP_303_SEE_OTHER)


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    request.session.clear()  # Очищаем сессию
    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)