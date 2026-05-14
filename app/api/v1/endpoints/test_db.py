from fastapi import APIRouter, Depends, Request

from app.shared.infra.database.db import get_db
from app.shared.middleware.limiter import limiter

router = APIRouter(tags=["test-db"])


@router.get("/test-db")
@limiter.limit("10/minute")
async def test_connection(request: Request, db=Depends(get_db)):
    try:
        result = await db.fetchrow("SELECT 1 AS ok;")
        return {
            "status": "success",
            "result": dict(result),
        }
    except Exception as error:
        return {
            "status": "failed",
            "error": str(error),
        }
