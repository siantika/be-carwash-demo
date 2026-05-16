import asyncpg

from app.modules.billing.domain.repositories.i_billing_uow import IBillingUnitOfWork
from app.modules.billing.infra.repositories.idempotency_repo import (
    AsyncPgIdempotencyRepository,
)
from app.modules.billing.infra.repositories.transaction_repo import (
    AsyncPgTransactionRepository,
)
from app.modules.carwash_operation.infra.repositories.ticket_repo import (
    AsyncPgTicketRepository,
)
from app.modules.identity.infra.repositories.account_repo import (
    AsyncPgAccountRepository,
)
from app.shared.interfaces.i_logger import ILogger


class AsyncPgBillingUnitOfWork(IBillingUnitOfWork):
    def __init__(self, pool: asyncpg.Pool, logger: ILogger):
        self._pool = pool
        self._conn: asyncpg.Connection | None = None
        self._tx: asyncpg.Transaction | None = None
        self._completed = False
        self.logger = logger

        self.transaction: AsyncPgTransactionRepository | None = None
        self.idempotency: AsyncPgIdempotencyRepository | None = None
        self.ticket: AsyncPgTicketRepository | None = None
        self.account: AsyncPgAccountRepository | None = None

    async def __aenter__(self) -> "AsyncPgBillingUnitOfWork":
        self._conn = await self._pool.acquire()
        self._tx = self._conn.transaction()

        await self._tx.start()

        self._completed = False

        self.transaction = AsyncPgTransactionRepository(self._conn, self.logger)
        self.idempotency = AsyncPgIdempotencyRepository(self._conn, self.logger)
        self.ticket = AsyncPgTicketRepository(self._conn, self.logger)
        self.account = AsyncPgAccountRepository(self._conn, self.logger)

        return self

    async def __aexit__(self, exc_type, exc, tb) -> bool:
        try:
            if self._tx is not None and not self._completed:
                await self._tx.rollback()
                self._completed = True
        finally:
            if self._conn is not None:
                await self._pool.release(self._conn)

            self._conn = None
            self._tx = None
            self._completed = False

            self.transaction = None
            self.idempotency = None
            self.ticket = None
            self.account = None

        return False

    async def commit(self) -> None:
        if self._tx is None:
            raise RuntimeError("Transaction has not been started")

        if not self._completed:
            await self._tx.commit()
            self._completed = True

    async def rollback(self) -> None:
        if self._tx is None:
            raise RuntimeError("Transaction has not been started")

        if not self._completed:
            await self._tx.rollback()
            self._completed = True