from app.api.dependencies import UserServiceDep  # type: ignore
from app.api.schemas.users import UserCreate, UserRead  # type: ignore
from app.services.users import UserAlreadyExistsError  # type: ignore
from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/users", tags=["User"])


# API 層負責 HTTP semantics
### Register a user
@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
async def register_user(
    user: UserCreate,
    service: UserServiceDep,
):
    try:
        # 回傳User (SQLModel instance), FastAPI 接下來會用 Pydantic 把 Users 轉成 UserRead(response_model)
        return await service.add(user)
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


### Login


### Logout
