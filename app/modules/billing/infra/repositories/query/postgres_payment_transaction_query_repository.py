from typing import Any

import asyncpg

from app.modules.billing.application.queries.models import (
    TransactionListFilterDto,
    TransactionRecord,
)
from app.modules.billing.application.queries.payment_transaction_query_repository import (
    IPaymentTransactionQueryRepository,
)
from app.modules.billing.infra.repositories.transaction_repo import _mapper
from app.shared.infra.database.error_handler import handle_db_error
from app.shared.interfaces.i_logger import ILogger


class PostgresPaymentTransactionQueryRepository(IPaymentTransactionQueryRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def list(
        self,
        *,
        filters: TransactionListFilterDto,
        limit: int,
        offset: int,
    ):
        async def _fetch():
            conditions: list[str] = []
            params: list[Any] = []

            if filters.ticket_id is not None:
                params.append(filters.ticket_id)
                conditions.append(f"tx.ticket_id = ${len(params)}")

            if filters.cashier_id is not None:
                params.append(filters.cashier_id)
                conditions.append(f"tx.cashier_id = ${len(params)}")

            if filters.payment_method is not None:
                params.append(filters.payment_method.value)
                conditions.append(f"tx.payment_method = ${len(params)}")

            if filters.payment_status is not None:
                params.append(filters.payment_status.value)
                conditions.append(f"tx.payment_status = ${len(params)}")

            if filters.plate_number is not None:
                params.append(f"%{filters.plate_number}%")
                conditions.append(f"tx.plate_number ILIKE ${len(params)}")

            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            limit_param = len(params) + 1
            offset_param = len(params) + 2

            rows = await self.db.fetch(
                f"""
                SELECT
                    tx.id,
                    tx.ticket_id,
                    tx.cashier_id,
                    tx.plate_number,
                    tx.payment_method,
                    tx.payment_metadata,
                    tx.subtotal_amount,
                    tx.total_amount,
                    tx.payment_status,
                    tx.paid_at,
                    tx.created_at,
                    tx.updated_at,
                    t.ticket_number,
                    a.username AS cashier
                FROM billing.payments tx
                JOIN carwash_operation.tickets t ON tx.ticket_id = t.id
                JOIN identity.accounts a ON tx.cashier_id = a.id
                {where_clause}
                ORDER BY tx.created_at DESC, tx.id DESC
                LIMIT ${limit_param} OFFSET ${offset_param};
                """,
                *params,
                limit,
                offset,
            )
            total = await self.db.fetchval(
                f"""
                SELECT COUNT(*)
                FROM billing.payments tx
                JOIN carwash_operation.tickets t ON tx.ticket_id = t.id
                JOIN identity.accounts a ON tx.cashier_id = a.id
                {where_clause};
                """,
                *params,
            )

            return [
                TransactionRecord(
                    transaction=_mapper(row),
                    ticket_number=row["ticket_number"],
                    cashier=row["cashier"],
                )
                for row in rows
            ], int(total or 0)

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={
                "ticket_id": filters.ticket_id,
                "cashier_id": filters.cashier_id,
                "payment_method": (
                    filters.payment_method.value
                    if filters.payment_method is not None
                    else None
                ),
                "payment_status": (
                    filters.payment_status.value
                    if filters.payment_status is not None
                    else None
                ),
                "plate_number": filters.plate_number,
                "limit": limit,
                "offset": offset,
            },
            operation_name="list billing transactions",
        )
