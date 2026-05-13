from app.modules.billing.application.dto.transaction_dto import (
    ProcessTransactionCmd,
    TransactionListFilterDto,
    TransactionListResultDto,
    TransactionResultDto,
)
from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.repositories.i_billing_uow import IBillingUnitOfWork
from app.modules.billing.domain.repositories.i_transaction_repo import ITransactionRepository
from app.modules.billing.domain.value_objects.payment import Payment, PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import (
    PaymentState,
    PaymentStatus,
)
from app.modules.billing.domain.value_objects.plate_number import PlateNumber
from app.modules.billing.domain.value_objects.transaction_amount import TransactionAmount
from app.modules.carwash_operation.domain.entities.ticket import TicketStatusEnum
from app.shared.domain.entities.base import _utcnow
from app.shared.domain.exceptions.exceptions import (
    BusinessRuleViolation,
    EntityAlreadyExists,
    EntityNotFound,
    FailedToSaveTransactionError,
    InvalidTicketStateError,
)


def _parse_payment_method(
    payment_method: PaymentMethodEnum | str | None,
) -> PaymentMethodEnum | None:
    if payment_method is None:
        return None

    if isinstance(payment_method, PaymentMethodEnum):
        return payment_method

    try:
        return PaymentMethodEnum(payment_method.strip().upper())
    except ValueError as exc:
        raise BusinessRuleViolation("Invalid payment method") from exc


def _parse_payment_status(
    payment_status: PaymentStatus | str | None,
) -> PaymentStatus | None:
    if payment_status is None:
        return None

    if isinstance(payment_status, PaymentStatus):
        return payment_status

    try:
        return PaymentStatus(payment_status.strip().upper())
    except ValueError as exc:
        raise BusinessRuleViolation("Invalid payment status") from exc


def _to_transaction_result(
    transaction: PaymentTransaction,
    *,
    ticket_number: str,
    cashier: str,
) -> TransactionResultDto:
    return TransactionResultDto(
        id=transaction.id,
        ticket_id=transaction.ticket_id,
        ticket_number=ticket_number,
        cashier_id=transaction.cashier_id,
        cashier=cashier,
        plate_number=transaction.plate_number.value,
        payment_method=transaction.payment.method.value,
        payment_metadata=transaction.payment.metadata,
        subtotal_amount=transaction.subtotal_amount.amount,
        total_amount=transaction.total_amount.amount,
        payment_status=transaction.payment_status.status.value,
        paid_at=transaction.payment_status.paid_at,
        created_at=transaction.created_at,
        updated_at=transaction.updated_at,
    )


class ProcessTransactionUseCase:
    def __init__(self, uow: IBillingUnitOfWork):
        self.uow = uow

    async def execute(self, cmd: ProcessTransactionCmd) -> TransactionResultDto:
        async with self.uow as u:
            ticket = await u.ticket.find_by_id(cmd.ticket_id)
            if ticket is None:
                raise EntityNotFound("Ticket", cmd.ticket_id)

            if ticket.status != TicketStatusEnum.IN_PROGRESS:
                raise InvalidTicketStateError(
                    f"Ticket is not in a payable state. Ticket status: {ticket.status.value}"
                )

            existing_transaction = await u.transaction.find_by_ticket_id(cmd.ticket_id)
            if existing_transaction is not None:
                raise EntityAlreadyExists("PaymentTransaction", cmd.ticket_id)

            cashier = await u.account.find_by_id(cmd.cashier_id)
            if cashier is None:
                raise EntityNotFound("Cashier", cmd.cashier_id)

            amount = TransactionAmount(subtotal=ticket.service_snapshot.service_price)
            payment = Payment(
                method=_parse_payment_method(cmd.payment_method),
                metadata=cmd.payment_metadata or {},
            )
            transaction = PaymentTransaction(
                ticket_id=cmd.ticket_id,
                cashier_id=cmd.cashier_id,
                payment=payment,
                payment_status=PaymentState(status=PaymentStatus.PAID, paid_at=_utcnow()),
                plate_number=PlateNumber(cmd.plate_number),
                subtotal_amount=amount.subtotal,
                total_amount=amount.total,
            )

            transaction = await u.transaction.add(transaction)
            if transaction is None:
                raise FailedToSaveTransactionError(
                    f"Failed to save transaction with ticket id {cmd.ticket_id}"
                )

            ticket.mark_paid()
            await u.ticket.save(ticket)
            await u.commit()

        return _to_transaction_result(
            transaction,
            ticket_number=ticket.ticket_number.value,
            cashier=cashier.username.value,
        )


class ListTransactionsUseCase:
    def __init__(self, transaction_repo: ITransactionRepository):
        self.transaction_repo = transaction_repo

    async def execute(
        self,
        filters: TransactionListFilterDto | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> TransactionListResultDto:
        if page < 1:
            raise BusinessRuleViolation("Page must be greater than or equal to 1")

        if limit < 1:
            raise BusinessRuleViolation("Limit must be greater than or equal to 1")

        filters = filters or TransactionListFilterDto()

        if filters.ticket_id is not None and filters.ticket_id < 1:
            raise BusinessRuleViolation("Ticket id must be greater than or equal to 1")

        if filters.cashier_id is not None and filters.cashier_id < 1:
            raise BusinessRuleViolation("Cashier id must be greater than or equal to 1")

        plate_number = filters.plate_number.strip().upper() if filters.plate_number else None
        if plate_number == "":
            plate_number = None

        offset = (page - 1) * limit
        records, total = await self.transaction_repo.list(
            ticket_id=filters.ticket_id,
            cashier_id=filters.cashier_id,
            payment_method=_parse_payment_method(filters.payment_method),
            payment_status=_parse_payment_status(filters.payment_status),
            plate_number=plate_number,
            limit=limit,
            offset=offset,
        )

        return TransactionListResultDto(
            items=[
                _to_transaction_result(
                    record.transaction,
                    ticket_number=record.ticket_number,
                    cashier=record.cashier,
                )
                for record in records
            ],
            total=total,
            page=page,
            limit=limit,
        )
