from dataclasses import dataclass

from app.modules.identity.domain.entities.account import RoleCode


@dataclass(frozen=True)
class AccountListFilterDto:
    role: RoleCode | str | None = None
    is_active: bool | None = None
