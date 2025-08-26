from flask_restful import Resource, reqparse
from sqlalchemy import text

# from utils_tobedelete.dbcon import engine
from werkzeug.security import check_password_hash

# from utils_dev.dbcon import engine
from common.utils.dbcon import engine


class Login(Resource):
    def post(self):
        # 解析傳入參數
        parser = reqparse.RequestParser()
        parser.add_argument(
            "email", type=str, required=True, help="Email cannot be blank"
        )
        parser.add_argument(
            "password", type=str, required=True, help="Password cannot be blank"
        )
        data = parser.parse_args()

        # 查詢使用者
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, password_hash, username FROM user_gpx.users WHERE email = :email"
                ),
                {"email": data["email"]},
            ).fetchone()

        if result is None:
            return {"message": "User not found"}, 404

        user_id, password_hash, username = result

        # 驗證密碼
        if not check_password_hash(password_hash, data["password"]):
            return {"message": "Invalid credentials"}, 401

        # 這裡可以產生 JWT 或 session token 回傳
        return {
            "message": "Login successful",
            "data": {
                "user_id": user_id,
                "username": username,
            },
        }, 200
