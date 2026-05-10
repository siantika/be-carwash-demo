import json
from typing import Any, Mapping, Optional, Union, cast

import asyncpg

from application.dto.transaction_dto import TransactionResultDto
from domain.entities.transaction import Transaction
from app.shared.domain.exceptions.exceptions import RepositoryError
from domain.repositories.i_transaction_repo import ITransactionRepository
from domain.value_object.money import Money
from domain.value_object.payment import Payment, PaymentMethodEnum
from domain.value_object.payment_state import PaymentState, PaymentStatus
from domain.value_object.plate_number import PlateNumber
from infra.error_handler import handle_db_error
from interfaces.i_logger import ILogger

Row = Union[asyncpg.Record, Mapping[str, Any]]

SELECT_ALL_COLUMNS = """
    id,
    ticket_id,
    user_id,
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
        raise RepositoryError("Transaction row is None")
    return dict(row) if not isinstance(row, dict) else dict(row)


def _ensure_payment_status(data: Mapping[str, Any]) -> PaymentStatus:
    try:
        return PaymentStatus(data["payment_status"])
    except (KeyError, ValueError) as exc:
        raise RepositoryError(
            f"Invalid payment_status from DB: {data.get('payment_status')}"
        ) from exc


def _ensure_payment_method(data: Mapping[str, Any]) -> PaymentMethodEnum:
    try:
        return PaymentMethodEnum(data["payment_method"])
    except (KeyError, ValueError) as exc:
        raise RepositoryError(
            f"Invalid payment_method from DB: {data.get('payment_method')}"
        ) from exc


def _normalize_payment_metadata(data: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize payment_metadata into dict.
    - If DB returns json/jsonb -> usually dict already.
    - If DB returns text -> parse JSON safely.
    """
    pm = data.get("payment_metadata")

    if isinstance(pm, str):
        try:
            data["payment_metadata"] = json.loads(pm)
        except json.JSONDecodeError:
            data["payment_metadata"] = {}
    elif pm is None:
        data["payment_metadata"] = {}
    elif isinstance(pm, dict):
        # already ok
        data["payment_metadata"] = pm
    else:
        # unexpected type (e.g., list) -> keep but ensure dict
        data["payment_metadata"] = pm if isinstance(pm, dict) else {}

    return data


def _mapper(row: Row) -> Transaction:
    data = _normalize_payment_metadata(_to_dict(row))

    payment_method = _ensure_payment_method(data)
    payment_status = _ensure_payment_status(data)

    plate_raw = data["plate_number"]
    plate_vo = PlateNumber(plate_raw)

    return Transaction(
        id=data["id"],
        ticket_id=data["ticket_id"],
        user_id=data["user_id"],
        plate_number=plate_vo,
        payment=Payment(
            method=payment_method,
            metadata=cast(dict, data.get("payment_metadata", {})),
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

    async def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        async def _fetch() -> Optional[Transaction]:
            
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM transactions
                WHERE id = $1
                """,
                transaction_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"transaction_id": transaction_id},
            operation_name="fetch transaction by id",
        )

    # NOTE:
    # Reminder: this is a query.
    # Move it to the `queries` folder (do not mix with commands).
    async def list(self, limit: int, offset: int) -> list[TransactionResultDto]:
        async def _get():
            rows = await self.db.fetch(
                """
                SELECT
                    ts.id,
                    t.ticket_number AS ticket_number,
                    u.username AS username,
                    ts.plate_number,
                    ts.payment_method,
                    ts.payment_metadata,
                    ts.subtotal_amount,
                    ts.total_amount,
                    ts.payment_status,
                    ts.paid_at,
                    ts.created_at,
                    ts.updated_at
                FROM transactions ts
                JOIN tickets t ON ts.ticket_id = t.id
                JOIN users u ON ts.user_id = u.id
                ORDER BY ts.created_at DESC, ts.id DESC
                LIMIT $1 OFFSET $2
                """,
                limit,
                offset,
            )

            return [
                TransactionResultDto(
                    id=row["id"],
                    ticket_number=row["ticket_number"],
                    cashier=row["username"],          
                    payment_method=row["payment_method"],
                    payment_metadata=json.loads(row["payment_metadata"]), # Convert to python 3 Dict from JSON
                    subtotal_amount=row["subtotal_amount"],
                    total_amount=row["total_amount"],
                    payment_status=row["payment_status"],
                    paid_at=row["paid_at"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

        return await handle_db_error(
            operation=_get,
            logger=self.logger,
            context={"limit": limit, "offset": offset},
            operation_name="list transactions",
        )

        
    async def get_by_ticket_id(self, ticket_id: int) -> Optional[Transaction]:
        async def _fetch() -> Optional[Transaction]:
            row = await self.db.fetchrow(
                f"""
                SELECT {SELECT_ALL_COLUMNS}
                FROM transactions
                WHERE ticket_id = $1
                """,
                ticket_id,
            )
            return _mapper(row) if row else None

        return await handle_db_error(
            operation=_fetch,
            logger=self.logger,
            context={"ticket_id": ticket_id},
            operation_name="fetch transaction by ticket id",
        )

    async def add(self, tx: Transaction) -> Transaction:
        async def _create() -> Transaction:
            row = await self.db.fetchrow(
                f"""
                INSERT INTO transactions (
                    ticket_id,
                    user_id,
                    payment_method,
                    payment_metadata,
                    subtotal_amount,
                    total_amount,
                    plate_number,
                    payment_status,
                    paid_at
                )
                VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9)
                RETURNING {SELECT_ALL_COLUMNS};
                """,
                tx.ticket_id,
                tx.user_id,
                tx.payment.method.value,          # Enum -> str
                json.dumps(tx.payment.metadata or {}), # json/jsonb recommended
                tx.subtotal_amount.amount,        # Money -> numeric
                tx.total_amount.amount,
                tx.plate_number.value,
                tx.payment_status.status.value,   # Enum -> str
                tx.payment_status.paid_at,
            )

            if row is None:
                raise RepositoryError("Failed to insert transaction (no row returned).")

            return _mapper(row)

        return await handle_db_error(
            operation=_create,
            logger=self.logger,
            context={"ticket_id": tx.ticket_id, "user_id": tx.user_id},
            operation_name="create transaction",
        )
