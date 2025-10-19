from fastapi import APIRouter, HTTPException
from geoalchemy2.shape import to_shape
from shapely.geometry import mapping
from sqlalchemy import text

from common.utils.dbcon import engine

router = APIRouter()


@router.get("/")
async def list_trails():
    """
    傳回所有官方路徑基本資料
    """
    try:
        with engine.connect() as conn:
            query_sql = """
                SELECT id, trail_name_ch, location_name, permit_required from paths.trails ORDER BY id
            """
            trails = conn.execute(text(query_sql)).all()
            result = [
                {
                    "id": t.id,
                    "name": t.trail_name_ch,
                    "location": t.location_name,
                    "difficulty": "-",
                    "permitRequired": t.permit_required,
                }
                for t in trails
            ]
        return {"message": "成功查到所有步道基本資料", "trails": result}, 200
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internel Server Error: {str(e)}")
        # return {"message": "伺服器錯誤", "error": str(e)}, 500
