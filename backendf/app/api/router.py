from app.api.routers import trails, users  # type: ignore
from fastapi import APIRouter

master_router = APIRouter()

master_router.include_router(users.router)
master_router.include_router(trails.router)
