from fastapi import APIRouter

from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.test_db import router as test_db_router
from app.modules.analytics.api.routes import router as analytics_router
from app.modules.billing.api.routes import router as billing_router
from app.modules.carwash_operation.api.routes import router as carwash_operation_router
from app.modules.identity.api.routes import account_router, auth_router
from app.modules.service_catalog.api.routes import router as service_catalog_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(test_db_router)
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(account_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(
    service_catalog_router,
    prefix="/service-types",
    tags=["service-catalog"],
)
api_router.include_router(
    carwash_operation_router,
    prefix="/tickets",
    tags=["carwash-operation"],
)
api_router.include_router(
    billing_router,
    prefix="/transactions",
    tags=["billing"],
)

api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
