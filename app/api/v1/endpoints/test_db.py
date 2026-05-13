from fastapi import APIRouter, Depends, Request

from app.shared.infra.database.db import get_db
from app.shared.middleware.limiter import limiter

router = APIRouter(tags=["test-db"])

@router.get("/test-db")
@limiter.limit("10/minute")
async def test_connection(request:Request,db=Depends(get_db)):
    try:
        result = await db.fetchrow("SELECT 1 AS ok;")  # async query
        return {
            "status": "success",
            "result": dict(result)  # convert ke dict agar JSON-friendly
        }
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
