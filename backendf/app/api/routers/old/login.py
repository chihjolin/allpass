from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, constr
from sqlalchemy import text
from werkzeug.security import check_password_hash

from common.utils.dbcon import async_engine
from common.utils.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)


# ---------------------------
# 定義請求資料模型 (取代 reqparse)
# ---------------------------
class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6)


@router.post("/", status_code=status.HTTP_200_OK)
async def login(user_data: LoginRequest):
    """
    使用者登入 API
    驗證 email / password 並回傳基本資料
    """

    query_sql = text(
        """
        SELECT id, password_hash, username
        FROM user_gpx.users
        WHERE email = :email
    """
    )
    try:
        async with async_engine.connect() as conn:
            result = await conn.execute(query_sql, {"email": user_data.email})
            user = result.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user_id, password_hash, username = user

        if not check_password_hash(password_hash, user_data.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # to-do: 可在這裡加入 JWT 產生邏輯
        logger.info(f"User '{username}' logged in successfully")

        return {
            "message": "Login Successful",
            "data": {"user_id": user_id, "username": username},
        }

    except HTTPException:
        # 讓 FastAPI 處理 401 / 404 類的 HTTPException
        raise

    except Exception as e:
        logger.exception("Login failed: %s", e)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {e}")
