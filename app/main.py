import uvicorn
from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers.views import pages
from routers.api_auth import router as auth_router
from routers.api_catalog import router as catalog_router
from routers.api_cart import router as cart_router


app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

#
app.include_router(pages.router)

app.include_router(auth_router)
app.include_router(cart_router)
app.include_router(catalog_router)



if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
