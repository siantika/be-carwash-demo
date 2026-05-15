from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.shared import RoleChecker
from app.modules.analytics.api.dependencies import (
    get_daily_revenue_use_case,
    get_dashboard_summary_use_case,
)
from app.modules.analytics.api.schemas import (
    DailyRevenueResponse,
    DashboardSummaryResponse,
)
from app.modules.analytics.application.use_cases.get_daily_revenue import (
    GetDailyRevenueUseCase,
)
from app.modules.analytics.application.use_cases.get_dashboard_summary import (
    GetDashboardSummaryUseCase,
)
from app.modules.identity.domain.entities.account import RoleCode
from app.shared.response import BaseResponse

router = APIRouter()

ANALYTICS_ROLES = [RoleCode.OWNER]


@router.get(
    "/dashboard-summary",
    response_model=BaseResponse[DashboardSummaryResponse],
)
async def get_dashboard_summary(
    target_date: Annotated[
        date,
        Query(
            description="Target date for dashboard summary",
            example="2026-05-15",
        ),
],
    usecase: Annotated[
        GetDashboardSummaryUseCase,
        Depends(get_dashboard_summary_use_case),
    ],
    user=Depends(RoleChecker(ANALYTICS_ROLES)),
):
    summary = await usecase.execute(target_date)

    return BaseResponse(data=summary)



@router.get(
    "/daily-revenue",
    response_model=BaseResponse[list[DailyRevenueResponse]],
)
async def get_daily_revenue(
    start_date: Annotated[
        date,
        Query(
            description="Target date for daily revenue",
            example="2026-05-15",
        ),
],
        end_date: Annotated[
        date,
        Query(
            description="Target date for daily revenue",
            example="2026-05-15",
        ),
    ],
        usecase: Annotated[
        GetDailyRevenueUseCase,
        Depends(get_daily_revenue_use_case),
    ],
    user=Depends(RoleChecker(ANALYTICS_ROLES)),
):
    daily_revenue = await usecase.execute(start_date, end_date)

    return BaseResponse(data=daily_revenue)