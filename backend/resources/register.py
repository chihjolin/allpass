from flask_restful import Resource, reqparse
from sqlalchemy import text
from utils.dbcon import engine
from werkzeug.security import generate_password_hash


class Registration(Resource):
    def post(self):
        # 解析輸入參數
        parser = reqparse.RequestParser()
        parser.add_argument(
            "username", type=str, required=True, help="Username is required"
        )
        parser.add_argument(
            "password", type=str, required=True, help="Password is required"
        )
        args = parser.parse_args()

        username = args["username"]
        password = args["password"]

        # 密碼 hash
        password_hash = generate_password_hash(password)

        # 使用 raw SQL 插入
        insert_sql = text(
            """
            INSERT INTO user_gpx.users (username, password)
            VALUES (:username, :password_hash)
            RETURNING id, username, created_at
        """
        )

        try:
            with engine.begin() as conn:  # 自動 commit/rollback
                result = conn.execute(
                    insert_sql, {"username": username, "password_hash": password_hash}
                )
                user = result.fetchone()

            return {
                "id": user.id,
                "username": user.username,
                "created_at": str(user.created_at),
            }, 201

        except Exception as e:
            return {"error": str(e)}, 400
