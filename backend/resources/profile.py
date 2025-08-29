from flask_restful import Resource
from sqlalchemy import text
from common.utils.dbcon import engine
import os

class Profile(Resource):
    def get(self, id):
        with engine.connect() as conn:
            query_sql= f"""
            SELECT file_name, trail_id, uploaded_at FROM user_gpx.gpx_uploads
            WHERE user_id = :user_id
            """

            profiles = conn.execute(text(query_sql), {"user_id": id}).all()

            result = [
                {
                    "file_name": os.path.splitext(p.file_name)[0],
                    "trail_id": p.trail_id,
                    "date": p.uploaded_at.date().isoformat() 
                }
                for p in profiles
            ]

        return result, 200