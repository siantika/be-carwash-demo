from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class RegisterUserCmd:
    username: str 
    role: str 
    plain_password: str 


@dataclass(frozen=True)
class ActivationStatusUserCmd:
    is_active: bool 
    
    
@dataclass(frozen=True)
class UserResultDto:
    id: int 
    username: str
    role: str 
    created_at: datetime 
    updated_at: datetime
    
    
        
