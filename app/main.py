from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.routers.auth import router as auth_router
from app.routers.catalog import router as catalog_router
from app.routers.cart import router as cart_router


app = FastAPI()


app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(catalog_router)


@app.get("/")
async def root():
    return {"message": "REST API интернет-магазина работает! Перейдите на /docs для просмотра документации."}
