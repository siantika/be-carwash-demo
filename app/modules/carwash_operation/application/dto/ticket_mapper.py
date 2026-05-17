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


def ticket_result_to_dict(result: TicketResultDto) -> dict:
    return {
        "id": result.id,
        "ticket_number": result.ticket_number,
        "entry_time": result.entry_time.isoformat(),
        "status": result.status,
        "service_type_id": result.service_type_id,
        "service_name": result.service_name,
        "service_desc": result.service_desc,
        "service_price": str(result.service_price),
        "created_at": result.created_at.isoformat(),
        "updated_at": result.updated_at.isoformat(),
    }
