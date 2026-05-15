from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies.shared import RoleChecker
from app.modules.analytics.api.dependencies import (
    get_dashboard_summary_use_case,
)
from app.modules.analytics.api.schemas import DashboardSummaryResponse
from app.modules.analytics.application.use_cases.get_daily_revenue import (
    GetDailyRevenueUseCase,
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
        GetDailyRevenueUseCase,
        Depends(get_dashboard_summary_use_case),
    ],
    user=Depends(RoleChecker(ANALYTICS_ROLES)),
):
    summary = await usecase.execute(target_date)

    return BaseResponse(data=summary)