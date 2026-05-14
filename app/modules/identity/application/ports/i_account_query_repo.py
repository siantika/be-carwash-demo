from typing import Protocol

from app.modules.identity.application.dto.account_dto import AccountListResultDto
from app.modules.identity.domain.entities.account import RoleCode


class IAccountQueryRepository(Protocol):
    async def list(
        self,
        role: RoleCode | str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> AccountListResultDto:
        pass 