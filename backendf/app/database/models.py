from datetime import datetime

from pydantic import EmailStr
from sqlmodel import Column, DateTime, Field, SQLModel, func


class Users(SQLModel, table=True):
    __table_args__ = {"schema": "user_gpx"}

    id: int | None = Field(default=None, primary_key=True)
    email: EmailStr
    username: str
    password_hash: str
    created_at: datetime | None = Field(
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )
    )
