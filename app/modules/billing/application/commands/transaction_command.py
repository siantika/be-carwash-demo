from app.modules.billing.application.dto.transaction_dto import (
    ProcessTransactionCmd,
    TransactionResultDto,
)
from app.modules.billing.application.dto.transaction_mapper import to_transaction_result
from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction
from app.modules.billing.domain.repositories.i_billing_uow import IBillingUnitOfWork
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
    EntityNotFound,
    FailedToSaveTransactionError,
    TicketAlreadyPaidError,
    TicketNotPayableError,
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


class ProcessTransactionUseCase:
    def __init__(self, uow: IBillingUnitOfWork):
        self.uow = uow

    async def execute(self, cmd: ProcessTransactionCmd) -> TransactionResultDto:
        async with self.uow as u:
            ticket = await u.ticket.find_by_id(cmd.ticket_id)
            if ticket is None:
                raise EntityNotFound("Ticket", cmd.ticket_id)

            if ticket.status != TicketStatusEnum.IN_PROGRESS:
                raise TicketNotPayableError(
                    f"Ticket is not in a payable state. Ticket status: {ticket.status.value}"
                )

            existing_transaction = await u.transaction.find_by_ticket_id(cmd.ticket_id)
            if existing_transaction is not None:
                raise TicketAlreadyPaidError(
                    f"Ticket {cmd.ticket_id} already has a payment transaction"
                )

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

        return to_transaction_result(
            transaction,
            ticket_number=ticket.ticket_number.value,
            cashier=cashier.username.value,
        )

