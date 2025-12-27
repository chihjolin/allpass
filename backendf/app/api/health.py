from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def health_check():
    """
    API Health Check
    """
    return {"status": "ok"}
