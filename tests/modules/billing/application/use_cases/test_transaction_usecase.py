from dataclasses import dataclass
from decimal import Decimal
from typing import Any

import pytest

from app.modules.billing.application.dto.transaction_dto import (
    ProcessTransactionCmd,
)
from app.modules.billing.application.services.i_request_hasher import IRequestHasher
from app.modules.billing.domain.entities.idempotency_record import IdempotencyRecord
from app.modules.billing.application.queries.models import (
    TransactionListFilterDto,
    TransactionRecord,
)
from app.modules.billing.application.commands.transaction_command import (
    ProcessTransactionUseCase,
)
from app.modules.billing.application.queries.transaction_query import ListTransactionsUseCase
from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.value_objects.payment import Payment, PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import (
    PaymentState,
    PaymentStatus,
)
from app.modules.billing.domain.value_objects.plate_number import PlateNumber
from app.modules.carwash_operation.domain.entities.ticket import Ticket, TicketStatusEnum
from app.modules.carwash_operation.domain.value_objects.entry_time import EntryTime
from app.modules.carwash_operation.domain.value_objects.service_snapshot import (
    ServiceSnapshot,
)
from app.modules.carwash_operation.domain.value_objects.ticket_number import TicketNumber
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    TicketAlreadyPaidError,
    TicketNotPayableError,
)
from app.shared.domain.value_objects.money import Money


@dataclass(frozen=True)
class UsernameStub:
    value: str


@dataclass
class AccountStub:
    id: int
    username: UsernameStub


def make_ticket(status: TicketStatusEnum = TicketStatusEnum.IN_PROGRESS) -> Ticket:
    return Ticket(
        id=1,
        service_type_id=1,
        service_snapshot=ServiceSnapshot(
            service_name="Basic Wash",
            service_desc="Basic exterior wash",
            service_price=Money(Decimal("50000")),
        ),
        ticket_number=TicketNumber("4006381333931"),
        entry_time=EntryTime(_utcnow()),
        status=status,
    )


class FakeTicketRepository:
    def __init__(self):
        self.tickets: dict[int, Ticket] = {}

    async def find_by_id(self, ticket_id: int) -> Ticket | None:
        return self.tickets.get(ticket_id)

    async def save(self, ticket: Ticket) -> Ticket:
        self.tickets[ticket.id] = ticket
        return ticket


class FakeAccountRepository:
    def __init__(self):
        self.accounts: dict[int, AccountStub] = {}

    async def find_by_id(self, cashier_id: int) -> AccountStub | None:
        return self.accounts.get(cashier_id)


class FakeTransactionRepository:
    def __init__(self):
        self.transactions: dict[int, PaymentTransaction] = {}
        self.next_id = 1

    async def find_by_id(self, transaction_id: int) -> PaymentTransaction | None:
        return self.transactions.get(transaction_id)

    async def find_by_ticket_id(self, ticket_id: int) -> PaymentTransaction | None:
        return next(
            (
                transaction
                for transaction in self.transactions.values()
                if transaction.ticket_id == ticket_id
            ),
            None,
        )

    async def list(
        self,
        *,
        filters: TransactionListFilterDto,
        limit: int,
        offset: int,
    ) -> tuple[list[TransactionRecord], int]:
        transactions = list(self.transactions.values())

        if filters.ticket_id is not None:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.ticket_id == filters.ticket_id
            ]

        if filters.cashier_id is not None:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.cashier_id == filters.cashier_id
            ]

        if filters.payment_method is not None:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.payment.method == filters.payment_method
            ]

        if filters.payment_status is not None:
            transactions = [
                transaction
                for transaction in transactions
                if transaction.payment_status.status == filters.payment_status
            ]

        if filters.plate_number is not None:
            transactions = [
                transaction
                for transaction in transactions
                if filters.plate_number in transaction.plate_number.value
            ]

        transactions.sort(key=lambda transaction: transaction.id or 0, reverse=True)
        records = [
            TransactionRecord(
                transaction=transaction,
                ticket_number="4006381333931",
                cashier="cashier_01",
            )
            for transaction in transactions[offset:offset + limit]
        ]
        return records, len(transactions)

    async def add(self, transaction: PaymentTransaction) -> PaymentTransaction:
        transaction.id = self.next_id
        self.next_id += 1
        self.transactions[transaction.id] = transaction
        return transaction


class FakeIdempotencyRepository:
    def __init__(self):
        self.records: dict[tuple[str, str], IdempotencyRecord] = {}
        self.next_id = 1

    async def find_by_scope_and_key(
        self,
        *,
        scope: str,
        idempotency_key: str,
    ) -> IdempotencyRecord | None:
        return self.records.get((scope, idempotency_key))

    async def create_processing(
        self,
        *,
        scope: str,
        idempotency_key: str,
        request_hash: str,
        expires_at,
    ) -> IdempotencyRecord:
        key = (scope, idempotency_key)
        if key in self.records:
            from app.shared.domain.exceptions.exceptions import EntityAlreadyExists

            raise EntityAlreadyExists("IdempotencyKey", idempotency_key)
        now = _utcnow()
        record = IdempotencyRecord(
            id=self.next_id,
            scope=scope,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            status="PROCESSING",
            response_payload=None,
            http_status=None,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )
        self.next_id += 1
        self.records[key] = record
        return record

    async def mark_completed(
        self,
        *,
        record_id: int,
        response_payload: dict,
        http_status: int,
    ) -> IdempotencyRecord:
        for key, record in self.records.items():
            if record.id == record_id:
                updated = IdempotencyRecord(
                    id=record.id,
                    scope=record.scope,
                    idempotency_key=record.idempotency_key,
                    request_hash=record.request_hash,
                    status="COMPLETED",
                    response_payload=response_payload,
                    http_status=http_status,
                    created_at=record.created_at,
                    updated_at=_utcnow(),
                    expires_at=record.expires_at,
                )
                self.records[key] = updated
                return updated
        raise AssertionError("record not found")


class FixedRequestHasher(IRequestHasher):
    def hash(self, payload: dict[str, Any]) -> str:
        return str(payload)


class FakeBillingUnitOfWork:
    def __init__(
        self,
        transaction_repo: FakeTransactionRepository,
        idempotency_repo: FakeIdempotencyRepository,
        ticket_repo: FakeTicketRepository,
        account_repo: FakeAccountRepository,
    ):
        self.transaction = transaction_repo
        self.idempotency = idempotency_repo
        self.ticket = ticket_repo
        self.account = account_repo
        self.committed = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def commit(self):
        self.committed = True

    async def rollback(self):
        self.committed = False


def make_uow() -> FakeBillingUnitOfWork:
    ticket_repo = FakeTicketRepository()
    account_repo = FakeAccountRepository()
    transaction_repo = FakeTransactionRepository()
    idempotency_repo = FakeIdempotencyRepository()
    ticket_repo.tickets[1] = make_ticket()
    account_repo.accounts[1] = AccountStub(id=1, username=UsernameStub("cashier_01"))
    return FakeBillingUnitOfWork(
        transaction_repo, idempotency_repo, ticket_repo, account_repo
    )


@pytest.mark.anyio
async def test_process_transaction_creates_transaction_and_marks_ticket_paid() -> None:
    uow = make_uow()

    result = await ProcessTransactionUseCase(uow, FixedRequestHasher()).execute(
        ProcessTransactionCmd(
            ticket_id=1,
            cashier_id=1,
            plate_number="DK123LL",
            payment_method=PaymentMethodEnum.CASH,
            payment_metadata={},
        ),
        idempotency_key="tx-1-key-0001",
    )

    assert result.id == 1
    assert result.cashier_id == 1
    assert result.cashier == "cashier_01"
    assert result.ticket_number == "4006381333931"
    assert result.total_amount == Decimal("50000")
    assert uow.ticket.tickets[1].status == TicketStatusEnum.PAID
    assert uow.committed is True


@pytest.mark.anyio
async def test_process_transaction_rejects_non_payable_ticket() -> None:
    uow = make_uow()
    uow.ticket.tickets[1] = make_ticket(TicketStatusEnum.PAID)

    with pytest.raises(TicketNotPayableError):
        await ProcessTransactionUseCase(uow, FixedRequestHasher()).execute(
            ProcessTransactionCmd(
                ticket_id=1,
                cashier_id=1,
                plate_number="DK123LL",
                payment_method=PaymentMethodEnum.CASH,
                payment_metadata={},
            ),
            idempotency_key="tx-1-key-0002",
        )


@pytest.mark.anyio
async def test_process_transaction_rejects_duplicate_ticket_payment() -> None:
    uow = make_uow()
    await uow.transaction.add(
        PaymentTransaction(
            ticket_id=1,
            cashier_id=1,
            plate_number=PlateNumber("DK123LL"),
            payment=Payment(method=PaymentMethodEnum.CASH, metadata={}),
            payment_status=PaymentState(status=PaymentStatus.PAID, paid_at=_utcnow()),
            subtotal_amount=Money(Decimal("50000")),
            total_amount=Money(Decimal("50000")),
        )
    )

    with pytest.raises(TicketAlreadyPaidError):
        await ProcessTransactionUseCase(uow, FixedRequestHasher()).execute(
            ProcessTransactionCmd(
                ticket_id=1,
                cashier_id=1,
                plate_number="DK123LL",
                payment_method=PaymentMethodEnum.CASH,
                payment_metadata={},
            ),
            idempotency_key="tx-1-key-0003",
        )


@pytest.mark.anyio
async def test_list_transactions_applies_filters() -> None:
    uow = make_uow()
    usecase = ProcessTransactionUseCase(uow, FixedRequestHasher())
    await usecase.execute(
        ProcessTransactionCmd(
            ticket_id=1,
            cashier_id=1,
            plate_number="DK123LL",
            payment_method=PaymentMethodEnum.CASH,
            payment_metadata={},
        ),
        idempotency_key="tx-1-key-0004",
    )

    result = await ListTransactionsUseCase(uow.transaction).execute(
        filters=TransactionListFilterDto(
            ticket_id=1,
            cashier_id=1,
            payment_method=PaymentMethodEnum.CASH,
            payment_status=PaymentStatus.PAID,
            plate_number="DK123",
        )
    )

    assert result.total == 1
    assert result.items[0].ticket_number == "4006381333931"
    assert result.items[0].cashier == "cashier_01"


@pytest.mark.anyio
async def test_process_transaction_replays_completed_response_for_same_idempotency_key() -> None:
    uow = make_uow()
    usecase = ProcessTransactionUseCase(uow, FixedRequestHasher())
    cmd = ProcessTransactionCmd(
        ticket_id=1,
        cashier_id=1,
        plate_number="DK123LL",
        payment_method=PaymentMethodEnum.CASH,
        payment_metadata={},
    )

    first = await usecase.execute(cmd, idempotency_key="tx-1-key-0005")
    second = await usecase.execute(cmd, idempotency_key="tx-1-key-0005")

    assert first.id == second.id
    assert len(uow.transaction.transactions) == 1


@pytest.mark.anyio
async def test_process_transaction_rejects_same_idempotency_key_different_payload() -> None:
    uow = make_uow()
    usecase = ProcessTransactionUseCase(uow, FixedRequestHasher())

    await usecase.execute(
        ProcessTransactionCmd(
            ticket_id=1,
            cashier_id=1,
            plate_number="DK123LL",
            payment_method=PaymentMethodEnum.CASH,
            payment_metadata={},
        ),
        idempotency_key="tx-1-key-0006",
    )

    with pytest.raises(BusinessRuleViolation):
        await usecase.execute(
            ProcessTransactionCmd(
                ticket_id=1,
                cashier_id=1,
                plate_number="DK999ZZ",
                payment_method=PaymentMethodEnum.CASH,
                payment_metadata={},
            ),
            idempotency_key="tx-1-key-0006",
        )
