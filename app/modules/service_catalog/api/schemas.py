from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CreateServiceTypeRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Name of the service type",
    )
    desc: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Description of the service type",
    )
    price: Decimal = Field(
        ...,
        gt=0,
        description="Service price",
    )
    is_active: bool = Field(
        default=True,
        description="Whether the service type is active and selectable",
    )
    is_primary: bool = Field(
        default=False,
        description="Whether this service type is primary",
    )

    class Config:
        extra = "forbid"


class UpdateServiceTypeRequest(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=3,
        max_length=50,
        description="Name of the service type",
    )
    desc: str | None = Field(
        default=None,
        min_length=5,
        max_length=255,
        description="Description of the service type",
    )
    price: Decimal | None = Field(
        default=None,
        gt=0,
        description="Service price",
    )
    is_active: bool | None = Field(
        default=None,
        description="Whether the service type is active and selectable",
    )
    is_primary: bool | None = Field(
        default=None,
        description="Whether this service type is primary",
    )

    class Config:
        extra = "forbid"


class ServiceTypeResponse(BaseModel):
    id: int = Field(..., ge=1)
    name: str
    desc: str
    price: Decimal
    is_active: bool
    is_primary: bool
    created_at: datetime
    updated_at: datetime
