import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.views import pages
from app.routers.ws_chat import router as ws_chat_router
from app.services.chat_service import chat_service
from app.routers.api_auth import router as auth_router
from app.routers.api_catalog import router as catalog_router
from app.routers.api_cart import router as cart_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    print("Закрытие WebSocket соединений...")
    for socket_id, ws in list(chat_service.active_connections.items()):
        try:
            await ws.close(code=1001, reason="Сервер остановлен")
        except Exception:
            pass


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

app.include_router(ws_chat_router)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
