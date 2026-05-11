from dataclasses import dataclass


@dataclass(frozen=True)
class AuthConfig:
    access_token_expire_hours: int
    refresh_token_expire_days: int
