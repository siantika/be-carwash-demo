from dataclasses import dataclass


@dataclass(frozen=True)
class AuthContextDto:
    user_id: int
    username: str
    role: str
