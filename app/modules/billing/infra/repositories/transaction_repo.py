import json
from typing import Any, Mapping, cast

import asyncpg

from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.repositories.i_transaction_repo import (
    ITransactionRepository,
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
from app.shared.interfaces.i_logger import ILogger

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
                raise EntityAlreadyExists(
                    "PaymentTransaction", transaction.ticket_id
                ) from exc

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
