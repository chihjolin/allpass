from typing import Annotated

from app.services.users import UserService  # type: ignore
from core.env import settings  # type: ignore
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from common.utils.dbcon import get_async_session as async_session_factory
from common.utils.dbcon import make_engines

# 1. 建立 Engines
sync_url, async_url, engine, async_engine = make_engines(
    host=settings.POSTGRES_HOST,
    port=settings.POSTGRES_PORT,
    db=settings.POSTGRES_DB,
    user=settings.POSTGRES_USER,
    password=settings.POSTGRES_PASSWORD,
)

# 2. 產生 Dependency Function
get_async_session = async_session_factory(async_engine)


# 3. 定義 Type Annotation(Asynchronous database session dep annotation)
SessionDep = Annotated[
    AsyncSession,
    Depends(get_async_session),  # 這裡放入產生好的 dependency function
]


# Service factory: User Service dep
def get_user_service(session: SessionDep) -> UserService:
    return UserService(session)


# Service dependency alias: User Service dep annotation
UserServiceDep = Annotated[
    UserService,
    Depends(get_user_service),
]
