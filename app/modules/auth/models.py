from pydantic import BaseModel, EmailStr

class User(BaseModel):
    id: int
    name: str
    email: str
    password: str

class UserRegister(BaseModel):
    name: str
    password: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str
