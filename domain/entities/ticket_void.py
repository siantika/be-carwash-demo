from dataclasses import Field, dataclass
from datetime import datetime
from typing import Optional

from app.shared.domain.entities.base import _utcnow

from app.shared.domain.exceptions.exceptions import InvalidValueObject


@dataclass(kw_only=True)
class TicketVoid:
    id: Optional[int] = None  
    ticket_id:int
    user_id:int  
    reason:str 
    void_time: datetime = _utcnow()
    
    
    def __post_init__(self):
        if not self.reason:
            raise InvalidValueObject("Reason cannot not be empty")
