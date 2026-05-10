from dataclasses import dataclass

from app.modules.identity.domain.entities.user import User


@dataclass(frozen=True)
class LoginResultDto:
    access_token:str 
    refresh_token: str
    token_type:str 
    user: User


@dataclass(frozen=True)
class TokenPairDto:
    access_token: str
    refresh_token: str
    token_type: str
