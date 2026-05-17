from datetime import datetime
from typing import Annotated
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.api.dependencies.shared import get_logger
from app.shared.middleware.limiter import limiter
from app.shared.interfaces.i_logger import ILogger

router = APIRouter()
WITA = ZoneInfo("Asia/Makassar")


@router.get("/health")
@limiter.limit("5/minute")
async def health_check(
    request: Request,
    logger: Annotated[ILogger, Depends(get_logger)],
):
    logger.info("Health check invoked")
    return JSONResponse(
        {
            "status": "OK",
            "server": "SERVERCARWASH",
            "time": datetime.now(WITA).isoformat(),
            "timezone": "WITA",
        }
    )
