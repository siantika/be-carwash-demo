from app.modules.carwash_operation.application.dto.ticket_dto import TicketResultDto
from app.modules.carwash_operation.domain.entities.ticket import Ticket


def to_ticket_result(ticket: Ticket) -> TicketResultDto:
    return TicketResultDto(
        id=ticket.id,
        ticket_number=ticket.ticket_number.value,
        entry_time=ticket.entry_time.value,
        status=ticket.status.value,
        service_type_id=ticket.service_type_id,
        service_name=ticket.service_snapshot.service_name,
        service_desc=ticket.service_snapshot.service_desc,
        service_price=ticket.service_snapshot.service_price.amount,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )

