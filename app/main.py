import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse

from app.config import templates
from app.routers.views import pages
from app.services.chat_service import manager
from app.websockets.ws_chat_routers import ws_router
from app.routers.api_auth import router as auth_router
from app.routers.api_catalog import router as catalog_router
from app.routers.api_cart import router as cart_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Тут могут быть твои коннекты к БД и т.д.
    yield
    print("Остановка сервера. Отключение WebSocket клиентов...")
    for socket_id, ws in list(manager.active_connections.items()):
        await ws.close(code=1001, reason="Сервер останавливается")


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

app.include_router(pages.router)

app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(catalog_router)

app.include_router(ws_router, tags=["WebSockets"])


@app.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
