from dataclasses import dataclass


@dataclass(frozen=True)
class TokenPairDto:
    access_token: str
    refresh_token: str
    token_type: str
