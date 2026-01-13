from pydantic import BaseModel, EmailStr


class BaseUser(BaseModel):
    email: EmailStr
    username: str


class UserCreate(BaseUser):
    password: str


class UserRead(BaseUser):
    pass


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
