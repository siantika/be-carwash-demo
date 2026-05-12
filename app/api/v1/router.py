from fastapi import APIRouter

from app.modules.identity.api.routes import account_router, auth_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(account_router, prefix="/accounts", tags=["accounts"])
