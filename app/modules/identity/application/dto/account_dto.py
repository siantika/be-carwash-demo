from dataclasses import dataclass
from datetime import datetime

from app.modules.identity.domain.entities.account import RoleCode


@dataclass(frozen=True)
class RegisterAccountCmd:
    username: str
    email: str
    password: str
    role: RoleCode | str
    is_active: bool = True


@dataclass(frozen=True)
class AccountResultDto:
    id: int | None
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class AccountListResultDto:
    items: list[AccountResultDto]
    total: int
    page: int
    limit: int
