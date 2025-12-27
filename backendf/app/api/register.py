from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import text
from werkzeug.security import generate_password_hash

from common.utils.dbcon import async_engine
from common.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---------------------------
# 定義請求資料模型 (取代 reqparse)
# ---------------------------
class RegisterRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)
    username: constr(min_length=3, max_length=50)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest):
    """
    使用者註冊 API
    """

    # 密碼 hash
    password_hash = generate_password_hash(user_data.password)

    # 使用 raw SQL 插入
    insert_sql = text(
        """
        INSERT INTO user_gpx.users (email, password_hash, username)
        VALUES (:email, :password_hash, :username)
        RETURNING id, username, created_at
    """
    )

    try:
        async with async_engine.begin() as conn:  # 自動 commit/rollback
            result = await conn.execute(
                insert_sql,
                {
                    "email": user_data.email,
                    "password_hash": password_hash,
                    "username": user_data.username,
                },
            )
            user = result.fetchone()
        if not user:
            raise HTTPException(status_code=500, detail="User creation failed")

        logger.info(f"User '{user.username}' registered successfully")
        return {
            "message": "User registered successfully",
            "data": {
                "id": user.id,
                "username": user.username,
                "created_at": str(user.created_at),
            },
        }

    except Exception as e:
        logger.exception("User registration failed: %s", e)
        raise HTTPException(status_code=400, detail=f"Registration failed: {e}")
