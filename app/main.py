import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.shared.config.settings import settings
from app.shared.error_handling.handlers import register_exception_handlers
from app.shared.infra.database.db import lifespan
from app.shared.middleware.limiter import limiter
from app.shared.middleware.logger import setup_logger
from app.shared.middleware.security_headers import SecurityHeadersMiddleware

setup_logger(json_format=False)  # set true for prod


app = FastAPI(
    lifespan=lifespan,
    title="Server Carwash API Demo",
    version="1.0.0",
    description="Backend for carwash automation",
    contact={"name": "sian", "email": "pawesisiantika98@gmail.com"},
)


# register middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins= settings.CORS_ORIGINS,
    allow_methods=settings.CORS_ALLOW_METHODS, 
    allow_headers= settings.CORS_ALLOW_HEADERS,
)
app.add_middleware(SecurityHeadersMiddleware)
app.include_router(api_router, prefix=settings.API_VERSION)
register_exception_handlers(app)


@app.get("/")
async def home():
    return {"message": "Carwash Server is active!", "docs": "/docs"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
