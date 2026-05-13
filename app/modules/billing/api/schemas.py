from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.billing.domain.value_objects.payment import PaymentMethodEnum


class ProcessTransactionRequest(BaseModel):
    ticket_id: int = Field(..., ge=1)
    plate_number: str = Field(
        ...,
        min_length=3,
        max_length=12,
        pattern=r"^[A-Za-z]{1,2}\s?\d{1,4}\s?[A-Za-z]{0,3}$",
    )
    payment_method: PaymentMethodEnum
    payment_metadata: dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "forbid"


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1)
    ticket_id: int = Field(..., ge=1)
    ticket_number: str
    cashier_id: int = Field(..., ge=1)
    cashier: str
    plate_number: str
    payment_method: str
    payment_metadata: dict[str, Any]
    subtotal_amount: Decimal = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)
    payment_status: str
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime
