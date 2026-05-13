from app.modules.carwash_operation.application.dto.ticket_dto import (
    TicketListResultDto,
)
from app.modules.carwash_operation.application.dto.ticket_mapper import to_ticket_result
from app.modules.carwash_operation.application.queries.models import TicketListFilterDto
from app.modules.carwash_operation.domain.entities.ticket import TicketStatusEnum
from app.shared.domain.exceptions.exceptions import BusinessRuleViolation


def _parse_ticket_status(status: TicketStatusEnum | str | None) -> TicketStatusEnum | None:
    if status is None:
        return None

    if isinstance(status, TicketStatusEnum):
        return status

    try:
        return TicketStatusEnum(status.strip().upper())
    except ValueError as exc:
        raise BusinessRuleViolation("Invalid ticket status") from exc


class ListTicketsUseCase:
    def __init__(self, ticket_query):
        self.ticket_query = ticket_query

    async def execute(
        self,
        filters: TicketListFilterDto | None = None,
        page: int = 1,
        limit: int = 20,
    ) -> TicketListResultDto:
        if page < 1:
            raise BusinessRuleViolation("Page must be greater than or equal to 1")

        if limit < 1:
            raise BusinessRuleViolation("Limit must be greater than or equal to 1")

        filters = filters or TicketListFilterDto()
        status = _parse_ticket_status(filters.status)
        ticket_number = filters.ticket_number.strip() if filters.ticket_number else None
        if ticket_number == "":
            ticket_number = None

        if filters.service_type_id is not None and filters.service_type_id < 1:
            raise BusinessRuleViolation("Service type id must be greater than or equal to 1")

        offset = (page - 1) * limit
        tickets, total = await self.ticket_query.list(
            filters=TicketListFilterDto(
                status=status,
                service_type_id=filters.service_type_id,
                ticket_number=ticket_number,
            ),
            limit=limit,
            offset=offset,
        )

        return TicketListResultDto(
            items=[to_ticket_result(ticket) for ticket in tickets],
            total=total,
            page=page,
            limit=limit,
        )

