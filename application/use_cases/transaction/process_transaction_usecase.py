from app.shared.domain.entities.base import _utcnow

from app.shared.domain.exceptions.exceptions import (
    EntityAlreadyExists,
    EntityNotFound,
    FailedToSaveTransactionError,
    InvalidTicketStateError,
)
from application.dto.transaction_dto import ProcessTransactionCmd, TransactionResultDto
from application.i_unit_of_work import IUnitOfWork
from domain.entities.ticket import TicketStatusEnum
from domain.entities.transaction import Transaction
from domain.value_object.payment import Payment, PaymentMethodEnum
from domain.value_object.payment_state import PaymentState, PaymentStatus
from domain.value_object.plate_number import PlateNumber
from domain.value_object.transaction_amount import TransactionAmount


class ProcessTransactionUseCase:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    async def execute(self, cmd: ProcessTransactionCmd) -> TransactionResultDto:
        async with self.uow as u:
            # 1. Ticket validation
            ticket = await u.ticket.get_by_id(cmd.ticket_id)
            if not ticket:
                raise EntityNotFound(f"Ticket with id {cmd.ticket_id} is not found")
            if ticket.status != TicketStatusEnum.IN_PROGRESS:
                raise InvalidTicketStateError(
                    f"Ticket is not in a payable state. Ticket status: {ticket.status}"
                )
            existing_tx = await u.transaction.get_by_ticket_id(cmd.ticket_id)
            if existing_tx:
                raise EntityAlreadyExists(
                    f"Ticket with id {cmd.ticket_id} already has a transaction"
                )
                
            cashier = await u.user.get_by_id(cmd.user_id)
                
            # 2. Calculate transaction amount
            ta = TransactionAmount(
                subtotal=ticket.service_snapshot.service_price
            )

            # 3. Create transaction
            # mock payment status. It's always success 
            mock_success_payment_state = PaymentState(status=PaymentStatus.PAID,
                                                      paid_at= _utcnow())
            
            payment = Payment(method=PaymentMethodEnum(cmd.payment_method), 
                              metadata= cmd.payment_metadata)
            
            transaction = Transaction(
                ticket_id=cmd.ticket_id,
                user_id=cmd.user_id,
                payment=payment,
                payment_status= mock_success_payment_state,
                plate_number=PlateNumber(cmd.plate_number),
                subtotal_amount=ta.subtotal,
                total_amount=ta.total,
            )

            transaction = await u.transaction.add(transaction)
            if not transaction:
                raise FailedToSaveTransactionError(
                    f"Failed to save transaction with ticket id {cmd.ticket_id}"
                )

            # 4. Set ticket status as Paid
            ticket.mark_paid()
            await u.ticket.save(ticket)
            await u.commit()  

            return TransactionResultDto(
                id = transaction.id,
                ticket_number= ticket.ticket_number.value,
                cashier= cashier.username,
                payment_method= transaction.payment.method.value,
                payment_metadata= transaction.payment.metadata,
                payment_status= transaction.payment_status.status.value,
                subtotal_amount= transaction.subtotal_amount.amount,
                total_amount= transaction.total_amount.amount,
                paid_at= transaction.payment_status.paid_at,
                created_at= transaction.created_at,
                updated_at= transaction.updated_at,                
            )
        
        
