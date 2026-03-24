from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import router

def main():
    app = FastAPI()
    app.mount("/static", StaticFiles(directory="static"), name="static")
    app.include_router(router)


if __name__ == '__main__':
    main()
