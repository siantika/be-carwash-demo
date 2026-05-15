from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):
    today_revenue: Decimal
    today_transactions: int
    active_tickets: int
    completed_tickets: int
    voided_transactions: int


class DailyRevenueResponse(BaseModel):
    date_at: date
    revenue: Decimal
    transaction_count: int


class TopServiceResponse(BaseModel):
    service_name: str
    total_sold: int
    total_revenue: Decimal


class PaymentMethodSummaryResponse(BaseModel):
    payment_method: str
    transaction_count: int
    total_amount: Decimal
