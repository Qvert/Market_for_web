from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.config import templates
from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.cart import router as cart_router


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(catalog_router)


@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse(
        request=request,
        name="404.html",
        context={"title": "Страница не найдена"},
        status_code=404
    )
