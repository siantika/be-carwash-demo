from datetime import date

from app.modules.analytics.application.dto import PaymentMethodSummaryDTO
from app.modules.analytics.application.ports.i_analytics_query_repo import (
    IAnalyticsQueryRepository,
)


class GetPaymentMethodSummaryUseCase:
    def __init__(self, analytics_query_repo: IAnalyticsQueryRepository):
        self.repo = analytics_query_repo

    async def execute(
        self, start_date: date, end_date: date
    ) -> PaymentMethodSummaryDTO:
        return await self.repo.get_payment_method_summary(start_date, end_date)
