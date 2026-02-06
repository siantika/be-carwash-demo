from dataclasses import dataclass

from domain.entities.user import User


@dataclass(frozen=True)
class LoginResultDto:
    access_token:str 
    token_type:str 
    user: User