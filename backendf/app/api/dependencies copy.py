from typing import Annotated

from app.services.users import UserService
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.dbcon import get_async_session

# Asynchronous database session dep annotation
SessiondDep = Annotated[
    AsyncSession,
    Depends(get_async_session),
]


# Service factory: User Service dep
def get_user_service(session: SessiondDep) -> UserService:
    return UserService(session)


# Service dependency alias: User Service dep annotation
UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]
