from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from app.api.dependencies.shared import get_logger
from app.shared.middleware.limiter import limiter
from interfaces.i_logger import ILogger

router = APIRouter()

@router.get("/health")
@limiter.limit("5/minute")
async def health_check(request:Request,
                       logger: ILogger = Depends(get_logger)):
    logger.info("Health check invoked")
    return JSONResponse({
        "status": "OK",
        "server": "SERVERCARWASH",
        "time": datetime.now().isoformat(),
        "timezone": "WITA"
    })
