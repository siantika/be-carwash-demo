from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TicketVoidRequest(BaseModel):
    """Schema for creating a ticket void request."""

    reason: str = Field(
        ..., min_length=3, max_length=255, description="Reason for voiding the ticket"
    )

    class Config:
        extra = "forbid"


class TicketVoidResponse(BaseModel):
    """Schema for ticket void response."""

    model_config = ConfigDict(from_attributes=True)
    id: int = Field(..., description="Ticket-void ID")
    ticket_number: str = Field(..., description="Voided ticket number")
    user_id: int = Field(
        ..., description="User-id that responsile for voided the ticket"
    )
    reason: str = Field(..., description="Reason for voiding the ticket")
    entry_time: datetime = Field(..., description="Ticket entry timestamp (UTC)")
    void_time: datetime = Field(..., description="Void timestamp (UTC)")
