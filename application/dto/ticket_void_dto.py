from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CreateTicketVoidCmd:
    ticket_id: int 
    user_id: int 
    reason: str 

    
    
@dataclass(frozen=True)
class TicketVoidResultDto:
    id: int 
    ticket_id: int 
    user_id: int 
    ticket_number: str 
    reason: str 
    entry_time: datetime 
    void_time: datetime
