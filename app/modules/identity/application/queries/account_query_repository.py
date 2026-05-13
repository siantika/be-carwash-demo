from typing import Protocol

from app.modules.identity.application.queries.models import AccountListFilterDto
from app.modules.identity.domain.entities.account import Account


class IAccountQueryRepository(Protocol):
    async def list(
        self,
        *,
        filters: AccountListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[Account], int]: ...
