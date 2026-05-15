from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class DashboardSummaryDTO:
    today_revenue: Decimal
    today_transactions: Decimal
    active_tickets: int
    completed_tickets: int
    voided_transactions: int 
    

@dataclass(frozen=True)
class DailyRevenueDTO:
    selected_date:date
    revenue: Decimal 
    transaction_count: int  


@dataclass(frozen=True)
class TopServiceDTO:
    service_name: str 
    total_sold: int 
    total_revenue: Decimal
    

@dataclass(frozen=True)
class PaymentMethodSummaryDTO:
    payment_method: str 
    transaction_count: int 
    total_amount: Decimal