from app.modules.billing.application.dto.transaction_dto import TransactionResultDto
from app.modules.billing.domain.entities.payment_transaction import PaymentTransaction


def to_transaction_result(
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

