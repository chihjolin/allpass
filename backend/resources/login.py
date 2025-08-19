from flask_restful import Resource, reqparse
from sqlalchemy import text
from utils.dbcon import engine
from werkzeug.security import check_password_hash


class Login(Resource):
    def post(self):
        # 解析傳入參數
        parser = reqparse.RequestParser()
        parser.add_argument(
            "username", type=str, required=True, help="Username cannot be blank"
        )
        parser.add_argument(
            "password", type=str, required=True, help="Password cannot be blank"
        )
        data = parser.parse_args()

        # 查詢使用者
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    "SELECT id, password FROM user_gpx.users WHERE username = :username"
                ),
                {"username": data["username"]},
            ).fetchone()

        if result is None:
            return {"message": "User not found"}, 404

        user_id, hashed_password = result

        # 驗證密碼
        if not check_password_hash(hashed_password, data["password"]):
            return {"message": "Invalid credentials"}, 401

        # TODO: 這裡可以產生 JWT 或 session token 回傳
        return {"message": "Login successful", "user_id": user_id}, 200
