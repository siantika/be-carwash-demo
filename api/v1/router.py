from fastapi import APIRouter

from app.modules.identity.api.routes import router as identity_router
from api.v1.endpoints import (
    health,
    service_type,
    test_db,
    ticket,
    transaction,
)

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(test_db.router, tags=["test-db"])
api_router.include_router(identity_router, prefix="/auth", tags=["auth"])
api_router.include_router(service_type.router, tags=['service-types'])
api_router.include_router(ticket.router, tags=['tickets'])
api_router.include_router(transaction.router, tags=['transactions'])
