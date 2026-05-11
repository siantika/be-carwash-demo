from fastapi import APIRouter

from app.modules.identity.api.routes import router as identity_router

api_router = APIRouter()
api_router.include_router(identity_router, prefix="/auth", tags=["auth"])
