from typing import Annotated

from asyncpg import Pool
from fastapi import Depends

from app.modules.analytics.application.ports.i_analytics_query_repo import (
    IAnalyticsQueryRepository,
)
from app.modules.analytics.application.use_cases.get_dashboard_summary import (
    GetDashboardSummaryUseCase,
)
from app.modules.analytics.infra.repositories.async_pg_analytics_query_repository import (
    AsyncPgAnalyticsQueryRepository,
)
from app.shared.infra.database.db import get_db
from app.shared.interfaces.i_logger import ILogger
from app.shared.middleware.logger import StructlogLogger


def get_logger() -> ILogger:
    return StructlogLogger("analytics")

def get_analytics_query_repository(db:Annotated[Pool, Depends(get_db)],
                                   logger: Annotated[ILogger, Depends(get_logger)]
                                   )-> IAnalyticsQueryRepository:
    return AsyncPgAnalyticsQueryRepository(db, logger)

def get_dashboard_summary_use_case(repo:Annotated[IAnalyticsQueryRepository,
                                                  Depends(get_analytics_query_repository) ]) -> GetDashboardSummaryUseCase:
    return GetDashboardSummaryUseCase(repo)





