import asyncpg

from app.modules.carwash_operation.domain.repositories.i_carwash_operation_uow import (
    ICarwashOperationUnitOfWork,
)
from app.modules.carwash_operation.infra.repositories.ticket_repo import (
    AsyncPgTicketRepository,
)
from app.modules.carwash_operation.infra.repositories.ticket_void_repo import (
    AsyncPgTicketVoidRepository,
)
from app.modules.identity.infra.repositories.account_repo import (
    AsyncPgAccountRepository,
)
from app.shared.interfaces.i_logger import ILogger


class AsyncPgCarwashOperationUnitOfWork(ICarwashOperationUnitOfWork):
    def __init__(self, pool: asyncpg.Pool, logger: ILogger):
        self._pool = pool
        self._conn: asyncpg.Connection | None = None
        self._tx: asyncpg.Transaction | None = None
        self._committed = False
        self.logger = logger

    async def __aenter__(self) -> "AsyncPgCarwashOperationUnitOfWork":
        self._conn = await self._pool.acquire()
        self._tx = self._conn.transaction()
        await self._tx.start()
        self._committed = False

        self.ticket = AsyncPgTicketRepository(self._conn, self.logger)
        self.ticket_void = AsyncPgTicketVoidRepository(self._conn, self.logger)
        self.account = AsyncPgAccountRepository(self._conn, self.logger)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is not None and self._tx is not None and not self._committed:
                await self._tx.rollback()
        finally:
            if self._conn is not None:
                await self._pool.release(self._conn)
            self._conn = None
            self._tx = None
            self._committed = False

        return False

    async def commit(self):
        if self._tx is not None and not self._committed:
            await self._tx.commit()
            self._committed = True

    async def rollback(self):
        if self._tx is not None and not self._committed:
            await self._tx.rollback()
            self._committed = True
