from dataclasses import dataclass


@dataclass(frozen=True)
class AuthContextDto:
    user_id:str
    username: str 
    role: str  
    