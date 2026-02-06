from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict


@dataclass(frozen=True)
class ProcessTransactionCmd:
    ticket_id: int
    user_id: int 
    plate_number: str
    payment_method: str
    payment_metadata: Dict[str, Any]
    

@dataclass(frozen=True)
class TransactionResultDto:
    id: int
    ticket_number: str 
    cashier: str 
    payment_method: str
    payment_metadata: Dict[str, Any]
    subtotal_amount: Decimal
    total_amount: Decimal
    payment_status: str
    paid_at: datetime
    created_at: datetime
    updated_at: datetime

