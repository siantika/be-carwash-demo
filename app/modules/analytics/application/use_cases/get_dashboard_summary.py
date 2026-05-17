from datetime import date

from app.modules.analytics.application.dto import DashboardSummaryDTO
from app.modules.analytics.application.ports.i_analytics_query_repo import (
    IAnalyticsQueryRepository,
)


class GetDashboardSummaryUseCase:
    def __init__(self, analytics_query_repo: IAnalyticsQueryRepository):
        self.repo = analytics_query_repo

    async def execute(self, target_date: date) -> DashboardSummaryDTO:
        return await self.repo.get_dashboard_summary(target_date)
