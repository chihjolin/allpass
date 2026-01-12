from fastapi import APIRouter

from backendf.app.api.schemas.users import UserCreate

router = APIRouter(prefix="/users")


### Register a user
@router.post("/register")
async def register_user(user: UserCreate):
    pass


### Login


### Logout
