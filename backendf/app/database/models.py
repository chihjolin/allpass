from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Field, SQLModel


class Users(SQLModel, table=True):
    __table_args__ = {"schema": "user_gpx"}

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr
    username: str
    password_hash: str
    created_at: datetime | None = None
