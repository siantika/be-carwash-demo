from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CreateTicketRequest(BaseModel):
    service_type_id: int = Field(..., ge=1, description="Service type ID")

    class Config:
        extra = "forbid"


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1)
    ticket_number: str
    entry_time: datetime
    status: str
    service_type_id: int = Field(..., ge=1)
    service_name: str
    service_desc: str
    service_price: Decimal
    created_at: datetime
    updated_at: datetime


class TicketVoidRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=255)

    class Config:
        extra = "forbid"


class TicketVoidResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., ge=1)
    ticket_id: int = Field(..., ge=1)
    ticket_number: str
    account_id: int = Field(..., ge=1)
    reason: str
    entry_time: datetime
    void_time: datetime
