from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.modules.billing.application.queries.payment_transaction_query_repository import (
    TransactionListFilterDto,
)
from app.modules.billing.domain.value_objects.payment import PaymentMethodEnum


@dataclass(frozen=True)
class ProcessTransactionCmd:
    ticket_id: int
    cashier_id: int
    plate_number: str
    payment_method: PaymentMethodEnum | str
    payment_metadata: dict[str, Any]


@dataclass(frozen=True)
class TransactionResultDto:
    id: int
    ticket_id: int
    ticket_number: str
    cashier_id: int
    cashier: str
    plate_number: str
    payment_method: str
    payment_metadata: dict[str, Any]
    subtotal_amount: Decimal
    total_amount: Decimal
    payment_status: str
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class TransactionListResultDto:
    items: list[TransactionResultDto]
    total: int
    page: int
    limit: int
