from datetime import date
from typing import Protocol

from app.modules.analytics.application.dto import (
    DailyRevenueDTO,
    DashboardSummaryDTO,
    PaymentMethodSummaryDTO,
    TopServiceDTO,
)


class IAnalyticsQueryRepository(Protocol):
    async def get_dashboard_summary(
        self,
        target_date: date,
    ) -> DashboardSummaryDTO:
        ...

    async def get_daily_revenue(
        self,
        start_date: date,
        end_date: date,
    ) -> list[DailyRevenueDTO]:
        ...

    async def get_top_services(
        self,
        start_date: date,
        end_date: date,
        limit: int,
    ) -> list[TopServiceDTO]:
        ...

    async def get_payment_method_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> list[PaymentMethodSummaryDTO]:
        ...