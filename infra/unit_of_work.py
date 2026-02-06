import asyncpg

from application.i_unit_of_work import IUnitOfWork
from infra.repositories.service_type_repo import AsyncPgServiceTypeRepository
from infra.repositories.ticket_repo import AsyncPgTicketRepository
from infra.repositories.ticket_void_repo import AsyncPgTicketVoidRepository
from infra.repositories.transaction_repo import AsyncPgTransactionRepository
from infra.repositories.user_repo import AsyncPgUserRepository
from interfaces.i_logger import ILogger


class AsyncpgUnitOfWork(IUnitOfWork):
    def __init__(self, pool: asyncpg.Pool, logger:ILogger):
        self._pool = pool
        self._conn: asyncpg.Connection | None = None
        self._tx: asyncpg.Transaction | None = None
        self._committed: bool = False
        self.logger = logger

    async def __aenter__(self) -> "AsyncpgUnitOfWork":
        self._conn = await self._pool.acquire()
        self._tx = self._conn.transaction()
        await self._tx.start()
        self._committed = False

        self.ticket = AsyncPgTicketRepository(self._conn, self.logger)
        self.ticket_void = AsyncPgTicketVoidRepository(self._conn, self.logger)
        self.transaction = AsyncPgTransactionRepository(self._conn, self.logger)
        self.service_type = AsyncPgServiceTypeRepository(self._conn, self.logger)
        self.user = AsyncPgUserRepository(self._conn, self.logger)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            # Only rollback when there is no commit and exception occured
            if exc_type is not None and self._tx is not None and not self._committed:
                try:
                    await self._tx.rollback()
                except Exception:
                    # Don't block primary error
                    pass
        finally:
            if self._conn is not None:
                await self._pool.release(self._conn)
            self._conn = None
            self._tx = None
            self._committed = False

        return False  # propagate exception

    async def commit(self):
        if self._tx is not None and not self._committed:
            await self._tx.commit()
            self._committed = True

    async def rollback(self):
        if self._tx is not None and not self._committed:
            await self._tx.rollback()
