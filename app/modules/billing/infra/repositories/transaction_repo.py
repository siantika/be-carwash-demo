import json
from typing import Any, Mapping, cast

import asyncpg

from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.repositories.i_transaction_repo import (
    ITransactionRepository,
    TransactionRecord,
)
from app.modules.billing.domain.value_objects.payment import Payment, PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import (
    PaymentState,
    PaymentStatus,
)
from app.modules.billing.domain.value_objects.plate_number import PlateNumber
from app.shared.domain.exceptions.exceptions import EntityAlreadyExists, RepositoryError
from app.shared.domain.value_objects.money import Money
from app.shared.infra.database.error_handler import handle_db_error
from interfaces.i_logger import ILogger

Row = asyncpg.Record | Mapping[str, Any]

SELECT_ALL_COLUMNS = """
id,
ticket_id,
cashier_id,
plate_number,
payment_method,
payment_metadata,
subtotal_amount,
total_amount,
payment_status,
paid_at,
created_at,
updated_at
""".strip()


def _to_dict(row: Row) -> dict[str, Any]:
    if row is None:
        raise RepositoryError("PaymentTransaction row is None")
    return dict(row) if not isinstance(row, dict) else dict(row)


def _normalize_payment_metadata(data: dict[str, Any]) -> dict[str, Any]:
    payment_metadata = data.get("payment_metadata")

    if isinstance(payment_metadata, str):
        try:
            data["payment_metadata"] = json.loads(payment_metadata)
        except json.JSONDecodeError:
            data["payment_metadata"] = {}
    elif payment_metadata is None:
        data["payment_metadata"] = {}
    elif not isinstance(payment_metadata, dict):
        data["payment_metadata"] = {}

    return data


def _mapper(row: Row) -> PaymentTransaction:
    data = _normalize_payment_metadata(_to_dict(row))

    try:
        payment_method = PaymentMethodEnum(data["payment_method"])
        payment_status = PaymentStatus(data["payment_status"])
    except (KeyError, ValueError) as exc:
        raise RepositoryError("Invalid transaction enum value from DB") from exc

    return PaymentTransaction(
        id=data["id"],
        ticket_id=data["ticket_id"],
        cashier_id=data["cashier_id"],
        plate_number=PlateNumber(data["plate_number"]),
        payment=Payment(
            method=payment_method,
            metadata=cast(dict[str, Any], data.get("payment_metadata", {})),
        ),
        subtotal_amount=Money(data["subtotal_amount"]),
        total_amount=Money(data["total_amount"]),
        payment_status=PaymentState(
            status=payment_status,
            paid_at=data["paid_at"],
        ),
        created_at=data["created_at"],
        updated_at=data["updated_at"],
    )


class AsyncPgTransactionRepository(ITransactionRepository):
    def __init__(self, db: asyncpg.Connection, logger: ILogger):
        self.db = db
        self.logger = logger

    async def find_by_id(self, transaction_id: int) -> PaymentTransaction | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM billing.payments
                WHERE id = $1;
                """,
                transaction_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"transaction_id": transaction_id},
            operation_name="fetch billing transaction by id",
        )

    async def find_by_ticket_id(self, ticket_id: int) -> PaymentTransaction | None:
        async def _fetch():
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM billing.payments
                WHERE ticket_id = $1;
                """,
                ticket_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"ticket_id": ticket_id},
            operation_name="fetch billing transaction by ticket id",
        )

    async def list(
        self,
        *,
        ticket_id: int | None,
        cashier_id: int | None,
        payment_method: PaymentMethodEnum | None,
        payment_status: PaymentStatus | None,
        plate_number: str | None,
        limit: int,
        offset: int,
    ) -> tuple[list[TransactionRecord], int]:
        async def _fetch():
            conditions: list[str] = []
            params: list[Any] = []

            if ticket_id is not None:
                params.append(ticket_id)
                conditions.append(f"tx.ticket_id = ${len(params)}")

            if cashier_id is not None:
                params.append(cashier_id)
                conditions.append(f"tx.cashier_id = ${len(params)}")

            if payment_method is not None:
                params.append(payment_method.value)
                conditions.append(f"tx.payment_method = ${len(params)}")

            if payment_status is not None:
                params.append(payment_status.value)
                conditions.append(f"tx.payment_status = ${len(params)}")

            if plate_number is not None:
                params.append(f"%{plate_number}%")
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
                "ticket_id": ticket_id,
                "cashier_id": cashier_id,
                "payment_method": payment_method.value if payment_method is not None else None,
                "payment_status": payment_status.value if payment_status is not None else None,
                "plate_number": plate_number,
                "limit": limit,
                "offset": offset,
            },
            operation_name="list billing transactions",
        )

    async def add(self, transaction: PaymentTransaction) -> PaymentTransaction:
        async def _create():
            try:
                row = await self.db.fetchrow(
                    f"""
                    INSERT INTO billing.payments (
                        ticket_id,
                        cashier_id,
                        payment_method,
                        payment_metadata,
                        subtotal_amount,
                        total_amount,
                        plate_number,
                        payment_status,
                        paid_at
                    )
                    VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9)
                    RETURNING {SELECT_ALL_COLUMNS};
                    """,
                    transaction.ticket_id,
                    transaction.cashier_id,
                    transaction.payment.method.value,
                    json.dumps(transaction.payment.metadata or {}),
                    transaction.subtotal_amount.amount,
                    transaction.total_amount.amount,
                    transaction.plate_number.value,
                    transaction.payment_status.status.value,
                    transaction.payment_status.paid_at,
                )
            except asyncpg.UniqueViolationError as exc:
                raise EntityAlreadyExists("PaymentTransaction", transaction.ticket_id) from exc

            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={
                "ticket_id": transaction.ticket_id,
                "cashier_id": transaction.cashier_id,
            },
            operation_name="create billing transaction",
        )
