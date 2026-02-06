from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateServiceTypeRequest(BaseModel):
    """Schema for creating a new service type."""

    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Name of the service type (e.g. Regular Wash, Premium Wash)"
    )

    desc: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Description of the service type"
    )

    price: Decimal = Field(
        ...,
        gt=0,
        description="Service price (must be greater than zero)"
    )

    is_primary: bool = Field(
        ...,
        description="Indicates whether this service is a primary service"
    )

    is_active: bool = Field(
        ...,
        description="Whether the service type is active and selectable"
    )

    class Config:
        extra = "forbid"   # Reject unexpected fields


class ServiceTypeResponse(BaseModel):
    """Schema for service type response."""

    id: int = Field(
        ...,
        ge=1,
        description="Unique identifier of the service type"
    )

    name: str = Field(
        ...,
        description="Name of the service type"
    )

    desc: str = Field(
        ...,
        description="Description of the service type"
    )

    price: Decimal = Field(
        ...,
        description="Service price"
    )

    is_active: bool = Field(
        ...,
        description="Whether the service type is active"
    )

    is_primary: bool = Field(
        ...,
        description="Indicates if this is a primary service"
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when the service type was created (UTC)"
    )

    updated_at: datetime = Field(
        ...,
        description="Timestamp when the service type was last updated (UTC)"
    )


