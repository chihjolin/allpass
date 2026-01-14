from app.api.dependencies import UserServiceDep  # type: ignore
from app.api.schemas.users import UserCreate, UserRead  # type: ignore
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["User"])


### Register a user
@router.post("/register", response_model=UserRead)
async def register_user(
    user: UserCreate,
    service: UserServiceDep,
):
    # 回傳User (SQLModel instance), FastAPI 接下來會用 Pydantic 把 User 轉成 UserRead(response_model)
    return await service.add(user)


### Login


### Logout
