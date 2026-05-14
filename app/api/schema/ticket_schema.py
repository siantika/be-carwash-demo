from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateTicketRequest(BaseModel):
    """Schema for creating a new ticket."""

    service_type_id: int = Field(..., ge=1, description="Service type ID")

    class Config:
        extra = "forbid"


class TicketResponse(BaseModel):
    """Schema for ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1, description="Ticket ID")
    ticket_number: str = Field(..., description="Ticket number (EAN-13)")
    entry_time: datetime = Field(..., description="Ticket entry timestamp (UTC)")
    status: str = Field(..., description="Ticket status (e.g., IN_PROGRESS/PAID/VOID)")

    service_type_id: int = Field(..., ge=1, description="Service type ID")
    service_name: str = Field(..., description="Service name snapshot")
    service_desc: str = Field(..., description="Service description snapshot")
    service_price: Decimal = Field(..., description="Service price snapshot")

    created_at: datetime = Field(..., description="Ticket created timestamp (UTC)")
    updated_at: datetime = Field(..., description="Ticket last updated timestamp (UTC)")
