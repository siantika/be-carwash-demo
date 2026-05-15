from datetime import date

from app.modules.analytics.application.dto import TopServiceDTO
from app.modules.analytics.application.ports.i_analytics_query_repo import (
    IAnalyticsQueryRepository,
)


class GetTopServicesUseCase:
    def __init__(self, analytics_query_repo:IAnalyticsQueryRepository):
        self.repo = analytics_query_repo
    
    async def execute(self, start_date:date, end_date:date, limit: int) -> TopServiceDTO:
        return await self.repo.get_top_service(
            start_date, end_date, limit
        )