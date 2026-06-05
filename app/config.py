import os
from pydantic_settings import BaseSettings
from fastapi.templating import Jinja2Templates

class Settings(BaseSettings):
    SECRET_KEY: str = "super-secret-key"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    RELOAD: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
templates = Jinja2Templates(directory="app/templates")