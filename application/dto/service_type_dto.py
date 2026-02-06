from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class CreateServiceTypeCmd:
    name:str 
    desc:str 
    price:Decimal
    is_active:bool
    is_primary:bool


@dataclass(frozen=True)
class UpdateServiceTypeCmd:
    name: Optional[str] = None
    desc: Optional[str] = None
    price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    is_primary: Optional[bool] = None 


@dataclass(frozen=True)
class ServiceTypeResultDto:
    id: int
    name: str
    desc: str
    price: Decimal
    is_active: bool
    is_primary: bool 
    created_at: datetime
    updated_at: datetime
