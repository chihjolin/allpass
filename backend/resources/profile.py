from flask_restful import Resource
from sqlalchemy import text
from common.utils.dbcon import engine
import os

class Profile(Resource):
    def get(self, id):
        with engine.connect() as conn:
            query_sql= f"""
            SELECT file_name, trail_id, uploaded_at, 
                   COALESCE(SUM(p.length_km), 0) AS total_length_km
            FROM user_gpx.gpx_uploads u
            LEFT JOIN paths.trails p ON u.trail_id = p.id
            WHERE user_id = :user_id
            GROUP BY u.trail_id, u.file_name, u.uploaded_at
            """

            profiles = conn.execute(text(query_sql), {"user_id": id}).all()

            result = [
                {
                    "file_name": os.path.splitext(p.file_name)[0],
                    "trail_id": p.trail_id,
                    "date": p.uploaded_at.date().isoformat(),
                    "total_length_km": float(p.total_length_km)
                }
                for p in profiles
            ]

        return result, 200