from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class ProcessTransactionRequest(BaseModel):
    """Schema for processing a transaction payment."""

    ticket_id: int = Field(..., gte=1, description="Ticket ID to be paid")

    plate_number: str = Field(
        ...,
        min_length=3,
        max_length=12,
        pattern=r"^[A-Z0-9]+$",
        description="Vehicle plate number (uppercase alphanumeric)",
    )

    payment_method: str = Field(
        ...,
        min_length=3,
        max_length=20,
        description="Payment method used (e.g. CASH, QRIS, CARD)",
    )

    payment_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional payment details depending on payment_method",
    )

    class Config:
        extra = "forbid"


class ProcessTransactionResponse(BaseModel):
    """Response schema after processing a transaction payment."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1, description="Transaction ID")
    ticket_number: str = Field(..., description="Related ticket number")
    cashier: str = Field(..., description="Username who processed the payment")

    payment_method: str = Field(
        ..., description="Payment method used (e.g. CASH, QRIS, CARD)"
    )
    payment_metadata: Dict[str, Any] = Field(..., description="Stored payment metadata")

    subtotal_amount: Decimal = Field(
        ..., ge=0, description="Subtotal amount before discounts"
    )
    total_amount: Decimal = Field(..., ge=0, description="Final amount paid")

    payment_status: str = Field(..., description="Payment status (e.g. PAID, FAILED)")
    paid_at: datetime = Field(..., description="Payment completion timestamp (UTC)")

    created_at: datetime = Field(..., description="Transaction created timestamp (UTC)")
    updated_at: datetime = Field(..., description="Transaction updated timestamp (UTC)")
