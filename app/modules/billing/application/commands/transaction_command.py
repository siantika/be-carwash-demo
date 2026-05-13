from datetime import datetime, timedelta
from decimal import Decimal

from app.modules.billing.application.dto.transaction_dto import (
    ProcessTransactionCmd,
    TransactionResultDto,
)
from app.modules.billing.application.dto.transaction_mapper import (
    to_transaction_result,
    transaction_result_to_dict,
)
from app.modules.billing.application.services.i_request_hasher import IRequestHasher
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
    EntityAlreadyExists,
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
    IDEMPOTENCY_SCOPE = "process_transaction"

    def __init__(self, uow: IBillingUnitOfWork, request_hasher: IRequestHasher):
        self.uow = uow
        self.request_hasher = request_hasher

    async def execute(
        self,
        cmd: ProcessTransactionCmd,
        *,
        idempotency_key: str,
    ) -> TransactionResultDto:
        key = idempotency_key.strip()
        if key == "":
            raise BusinessRuleViolation("Idempotency key is required")

        payment_method = _parse_payment_method(cmd.payment_method)
        request_hash = self.request_hasher.hash(
            {
                "ticket_id": cmd.ticket_id,
                "cashier_id": cmd.cashier_id,
                "plate_number": cmd.plate_number.strip().upper(),
                "payment_method": payment_method.value if payment_method else None,
                "payment_metadata": cmd.payment_metadata or {},
            }
        )

        async with self.uow as u:
            existing = await u.idempotency.find_by_scope_and_key(
                scope=self.IDEMPOTENCY_SCOPE,
                idempotency_key=key,
            )
            if existing is not None:
                if existing.request_hash != request_hash:
                    raise BusinessRuleViolation(
                        "Idempotency key already used with a different request payload"
                    )
                if existing.status == "COMPLETED" and existing.response_payload is not None:
                    payload = existing.response_payload
                    return TransactionResultDto(
                        id=int(payload["id"]),
                        ticket_id=int(payload["ticket_id"]),
                        ticket_number=str(payload["ticket_number"]),
                        cashier_id=int(payload["cashier_id"]),
                        cashier=str(payload["cashier"]),
                        plate_number=str(payload["plate_number"]),
                        payment_method=str(payload["payment_method"]),
                        payment_metadata=dict(payload["payment_metadata"]),
                        subtotal_amount=Decimal(str(payload["subtotal_amount"])),
                        total_amount=Decimal(str(payload["total_amount"])),
                        payment_status=str(payload["payment_status"]),
                        paid_at=(
                            datetime.fromisoformat(payload["paid_at"])
                            if payload["paid_at"] is not None
                            else None
                        ),
                        created_at=datetime.fromisoformat(payload["created_at"]),
                        updated_at=datetime.fromisoformat(payload["updated_at"]),
                    )
                raise BusinessRuleViolation("Idempotency key is currently being processed")

            try:
                idempotency = await u.idempotency.create_processing(
                    scope=self.IDEMPOTENCY_SCOPE,
                    idempotency_key=key,
                    request_hash=request_hash,
                    expires_at=_utcnow() + timedelta(hours=24),
                )
            except EntityAlreadyExists:
                raise BusinessRuleViolation("Idempotency key is currently being processed")

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
                method=payment_method,
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
            result = to_transaction_result(
                transaction,
                ticket_number=ticket.ticket_number.value,
                cashier=cashier.username.value,
            )
            await u.idempotency.mark_completed(
                record_id=idempotency.id,
                response_payload=transaction_result_to_dict(result),
                http_status=201,
            )
            await u.commit()
        return result
