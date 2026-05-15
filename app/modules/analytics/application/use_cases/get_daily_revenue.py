from datetime import date

from app.modules.analytics.application.dto import DailyRevenueDTO
from app.modules.analytics.application.ports.i_analytics_query_repo import (
    IAnalyticsQueryRepository,
)


class GetDailyRevenueUseCase:
    def __init__(self, analytics_query_repo:IAnalyticsQueryRepository):
        self.repo = analytics_query_repo
    
    async def execute(self, start_date:date, target_date:date) -> DailyRevenueDTO:
        return await self.repo.get_daily_revenue(
            start_date,
            target_date
        )