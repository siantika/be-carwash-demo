from app.modules.billing.application.dto.transaction_dto import (
    TransactionListResultDto,
)
from app.modules.billing.application.dto.transaction_mapper import to_transaction_result
from app.modules.billing.application.queries.models import TransactionListFilterDto
from app.modules.billing.domain.value_objects.payment import PaymentMethodEnum
from app.modules.billing.domain.value_objects.payment_state import PaymentStatus
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


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


class ListTransactionsUseCase:
    def __init__(self, transaction_query):
        self.transaction_query = transaction_query

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
        records, total = await self.transaction_query.list(
            filters=TransactionListFilterDto(
                ticket_id=filters.ticket_id,
                cashier_id=filters.cashier_id,
                payment_method=_parse_payment_method(filters.payment_method),
                payment_status=_parse_payment_status(filters.payment_status),
                plate_number=plate_number,
            ),
            limit=limit,
            offset=offset,
        )

        return TransactionListResultDto(
            items=[
                to_transaction_result(
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

