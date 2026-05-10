from app.shared.domain.exceptions.exceptions import EntityNotFound
from application.dto.ticket_void_dto import CreateTicketVoidCmd, TicketVoidResultDto
from application.i_unit_of_work import IUnitOfWork
from domain.entities.ticket_void import TicketVoid


class VoidTicketUseCase:
    def __init__(
        self,
        uow:IUnitOfWork
    ):
        self.uow  = uow 

    async def execute(self, cmd: CreateTicketVoidCmd) -> TicketVoidResultDto:
        async with self.uow as u:
            # check ticket  and mark as void
            ticket = await u.ticket.get_by_id(cmd.ticket_id)
            if ticket is None:
                raise EntityNotFound(f"Ticket with id: {cmd.ticket_id} is not found")
        
            voided_by_user = await u.user.get_by_id(cmd.user_id)
            if voided_by_user is None:
                raise EntityNotFound(f"user with id: {cmd.user_id} is not found")
            
            ticket.mark_void()
            await u.ticket.save(ticket)

            ticket_void = await u.ticket_void.add(
                TicketVoid(
                    ticket_id= ticket.id,
                    user_id= cmd.user_id,
                    reason= cmd.reason
                    # void time is automatically generated when ticket-void just created
                )
            )
            await u.commit()
            
            return TicketVoidResultDto(
                id = ticket_void.id,
                ticket_id= ticket_void.ticket_id,
                user_id= ticket_void.user_id,
                ticket_number= ticket.ticket_number.value,
                reason= ticket_void.reason,
                entry_time= ticket.entry_time.value,
                void_time= ticket_void.void_time
            )
            

        
