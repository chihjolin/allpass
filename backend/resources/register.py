from flask_restful import Resource, reqparse
from sqlalchemy import text
from werkzeug.security import generate_password_hash

# from utils_dev.dbcon import engine
# from utils_tobedelete.dbcon import engine
from common.utils.dbcon import engine

# from common.utils.dbcon import engine


class RegisterUser(Resource):
    def post(self):
        # 解析輸入參數
        parser = reqparse.RequestParser()
        parser.add_argument("email", type=str, required=True, help="Email is required")
        parser.add_argument(
            "password", type=str, required=True, help="Password is required"
        )
        parser.add_argument(
            "username", type=str, required=True, help="Username is required"
        )
        args = parser.parse_args()

        email = args["email"]
        password = args["password"]
        username = args["username"]

        # 密碼 hash
        password_hash = generate_password_hash(password)

        # 使用 raw SQL 插入
        insert_sql = text(
            """
            INSERT INTO user_gpx.users (email, password_hash, username)
            VALUES (:email, :password_hash, :username)
            RETURNING id, username, created_at
        """
        )

        try:
            with engine.begin() as conn:  # 自動 commit/rollback
                result = conn.execute(
                    insert_sql,
                    {
                        "email": email,
                        "password_hash": password_hash,
                        "username": username,
                    },
                )
                user = result.fetchone()

            return {
                "message": "User registered successfully",
                "data": {
                    "id": user.id,
                    "username": user.username,
                    "created_at": str(user.created_at),
                },
            }, 201

        except Exception as e:
            return {"error": str(e)}, 400
            return {"error": str(e)}, 400
