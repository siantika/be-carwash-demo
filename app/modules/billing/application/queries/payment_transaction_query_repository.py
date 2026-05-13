from typing import Protocol

from app.modules.billing.application.queries.models import (
    TransactionListFilterDto,
    TransactionRecord,
)


class IPaymentTransactionQueryRepository(Protocol):
    async def list(
        self,
        *,
        filters: TransactionListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[TransactionRecord], int]: ...
